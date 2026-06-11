package dev.spyc0der.minecraftscript;

import java.io.Closeable;
import java.io.IOException;
import java.nio.file.ClosedWatchServiceException;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.StandardWatchEventKinds;
import java.nio.file.WatchEvent;
import java.nio.file.WatchKey;
import java.nio.file.WatchService;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

public final class McsPackWatcher implements Closeable {
    private static final long PACK_SETTLE_MILLIS = 150;
    private static final long PACK_MAX_WAIT_MILLIS = 400;
    private static final long RELOAD_SETTLE_MILLIS = 75;
    private static final long MTIME_POLL_INTERVAL_MILLIS = 200;

    private final McsWorldPackManager packManager;
    private final McsServerAccess serverAccess;
    private final List<Path> watchedRoots;
    private final WatchService watchService;
    private final Map<WatchKey, Path> keys = new ConcurrentHashMap<>();
    private final Map<Path, ScheduledFuture<?>> pendingCompiles = new ConcurrentHashMap<>();
    private final Map<Path, Long> firstChangeAt = new ConcurrentHashMap<>();
    private final Map<Path, Long> lastSeenMtime = new ConcurrentHashMap<>();
    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor(runnable -> {
        Thread thread = new Thread(runnable, "mcs-pack-watcher-scheduler");
        thread.setDaemon(true);
        return thread;
    });
    private final ExecutorService compileExecutor = Executors.newSingleThreadExecutor(runnable -> {
        Thread thread = new Thread(runnable, "mcs-pack-watcher-compiler");
        thread.setDaemon(true);
        return thread;
    });
    private final AtomicBoolean reloadPending = new AtomicBoolean(false);
    private final Thread watcherThread;
    private volatile boolean running = true;

    public McsPackWatcher(McsWorldPackManager packManager, McsServerAccess serverAccess) throws IOException {
        this.packManager = packManager;
        this.serverAccess = serverAccess;
        this.watchedRoots = packManager.watchedMcsRoots();
        this.watchService = packManager.worldMcsRoot().getFileSystem().newWatchService();
        for (Path root : watchedRoots) {
            registerRecursively(root);
        }
        seedPackMtines();
        scheduler.scheduleAtFixedRate(
                this::pollPackMtines,
                MTIME_POLL_INTERVAL_MILLIS,
                MTIME_POLL_INTERVAL_MILLIS,
                TimeUnit.MILLISECONDS
        );
        this.watcherThread = new Thread(this::watchLoop, "mcs-pack-watcher");
        this.watcherThread.setDaemon(true);
    }

    public void start() {
        watcherThread.start();
    }

    static long computeCompileDelayMillis(long firstChangeAtMillis, long nowMillis) {
        long elapsed = nowMillis - firstChangeAtMillis;
        if (elapsed >= PACK_MAX_WAIT_MILLIS) {
            return 0;
        }
        return Math.min(PACK_SETTLE_MILLIS, PACK_MAX_WAIT_MILLIS - elapsed);
    }

    private void watchLoop() {
        while (running) {
            WatchKey key;
            try {
                key = watchService.take();
            } catch (ClosedWatchServiceException ignored) {
                return;
            } catch (InterruptedException ignored) {
                Thread.currentThread().interrupt();
                return;
            }

            Path directory = keys.get(key);
            if (directory == null) {
                key.reset();
                continue;
            }

            for (WatchEvent<?> event : key.pollEvents()) {
                if (event.kind() == StandardWatchEventKinds.OVERFLOW) {
                    scheduleFullScan();
                    continue;
                }

                Path changed = directory.resolve((Path) event.context());
                if (shouldIgnoreChange(changed)) {
                    continue;
                }

                if (event.kind() == StandardWatchEventKinds.ENTRY_CREATE && Files.isDirectory(changed)) {
                    try {
                        registerRecursively(changed);
                    } catch (IOException error) {
                        System.out.println("[Minecraft Script] Could not watch " + changed + ": " + error.getMessage());
                    }
                }

                Optional<Path> packFolder = McsPaths.packFolderForChangedPath(watchedRoots, changed);
                packFolder.ifPresent(this::schedulePackRefresh);
            }

            if (!key.reset()) {
                keys.remove(key);
            }
        }
    }

    private void scheduleFullScan() {
        scheduler.schedule(() -> compileExecutor.execute(() -> {
            if (packManager.compileAll()) {
                scheduleReload();
            }
        }), PACK_SETTLE_MILLIS, TimeUnit.MILLISECONDS);
    }

    private void schedulePackRefresh(Path packFolder) {
        Path normalized = packFolder.toAbsolutePath().normalize();
        try {
            Optional<McsPackEntry> entry = packManager.findPackEntry(packFolder.getFileName().toString());
            if (entry.isEmpty()
                    || !packManager.isPackEnabled(entry.get())
                    || !packManager.isHotReloadEnabledForPack(entry.get())) {
                return;
            }
        } catch (IOException error) {
            System.out.println("[Minecraft Script] Could not resolve pack for " + packFolder + ": " + error.getMessage());
            return;
        }

        long now = System.currentTimeMillis();
        if (firstChangeAt.putIfAbsent(normalized, now) == null) {
            packManager.notifyPackChangePending(packFolder);
        }

        ScheduledFuture<?> existing = pendingCompiles.remove(normalized);
        if (existing != null) {
            existing.cancel(false);
        }

        long delay = computeCompileDelayMillis(firstChangeAt.get(normalized), now);
        ScheduledFuture<?> future = scheduler.schedule(() -> compileExecutor.execute(() -> {
            pendingCompiles.remove(normalized);
            firstChangeAt.remove(normalized);
            if (packManager.refreshPack(normalized)) {
                scheduleReload();
            }
        }), delay, TimeUnit.MILLISECONDS);
        pendingCompiles.put(normalized, future);
    }

    private void scheduleReload() {
        if (!reloadPending.compareAndSet(false, true)) {
            return;
        }
        scheduler.schedule(() -> {
            reloadPending.set(false);
            serverAccess.executeReload();
        }, RELOAD_SETTLE_MILLIS, TimeUnit.MILLISECONDS);
    }

    private void seedPackMtines() {
        try {
            for (McsPackEntry entry : packManager.discoverPackEntries()) {
                if (packManager.isPackEnabled(entry) && packManager.isHotReloadEnabledForPack(entry)) {
                    rememberPackMtime(entry.packFolder());
                }
            }
        } catch (IOException error) {
            System.out.println("[Minecraft Script] Could not seed pack mtimes: " + error.getMessage());
        }
    }

    private void pollPackMtines() {
        if (!running) {
            return;
        }
        try {
            for (McsPackEntry entry : packManager.discoverPackEntries()) {
                if (!packManager.isPackEnabled(entry) || !packManager.isHotReloadEnabledForPack(entry)) {
                    continue;
                }
                Path packFolder = entry.packFolder();
                Path packFile = packFolder.resolve(McsPaths.PACK_FILE);
                if (!Files.isRegularFile(packFile)) {
                    continue;
                }
                long mtime = Files.getLastModifiedTime(packFile).toMillis();
                Path normalized = packFolder.toAbsolutePath().normalize();
                Long previous = lastSeenMtime.get(normalized);
                if (previous != null && mtime > previous) {
                    lastSeenMtime.put(normalized, mtime);
                    schedulePackRefresh(packFolder);
                    continue;
                }
                lastSeenMtime.put(normalized, mtime);
            }
        } catch (IOException error) {
            System.out.println("[Minecraft Script] Could not poll pack mtimes: " + error.getMessage());
        }
    }

    private void rememberPackMtime(Path packFolder) throws IOException {
        Path packFile = packFolder.resolve(McsPaths.PACK_FILE);
        if (!Files.isRegularFile(packFile)) {
            return;
        }
        Path normalized = packFolder.toAbsolutePath().normalize();
        lastSeenMtime.put(normalized, Files.getLastModifiedTime(packFile).toMillis());
    }

    private static boolean shouldIgnoreChange(Path changed) {
        String fileName = changed.getFileName().toString();
        return fileName.endsWith("~")
                || fileName.endsWith(".swp")
                || fileName.endsWith(".tmp")
                || fileName.startsWith(".#")
                || fileName.equals(McsModConfig.CONFIG_FILE);
    }

    private void registerRecursively(Path root) throws IOException {
        if (!Files.isDirectory(root)) {
            return;
        }
        Files.walkFileTree(root, new SimpleFileVisitor<>() {
            @Override
            public FileVisitResult preVisitDirectory(Path directory, BasicFileAttributes attrs) throws IOException {
                WatchKey key = directory.register(
                        watchService,
                        StandardWatchEventKinds.ENTRY_CREATE,
                        StandardWatchEventKinds.ENTRY_MODIFY,
                        StandardWatchEventKinds.ENTRY_DELETE
                );
                keys.put(key, directory);
                return FileVisitResult.CONTINUE;
            }
        });
    }

    @Override
    public void close() throws IOException {
        running = false;
        for (ScheduledFuture<?> future : new HashMap<>(pendingCompiles).values()) {
            future.cancel(false);
        }
        scheduler.shutdownNow();
        compileExecutor.shutdownNow();
        watchService.close();
    }
}
