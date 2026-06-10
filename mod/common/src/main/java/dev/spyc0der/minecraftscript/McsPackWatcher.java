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
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

public final class McsPackWatcher implements Closeable {
    private static final long COMPILE_DEBOUNCE_MILLIS = 750;
    private static final long RELOAD_DEBOUNCE_MILLIS = 250;

    private final McsWorldPackManager packManager;
    private final McsServerAccess serverAccess;
    private final WatchService watchService;
    private final Map<WatchKey, Path> keys = new ConcurrentHashMap<>();
    private final Map<Path, ScheduledFuture<?>> pendingCompiles = new ConcurrentHashMap<>();
    private final ScheduledExecutorService executor = Executors.newSingleThreadScheduledExecutor(runnable -> {
        Thread thread = new Thread(runnable, "mcs-pack-watcher-worker");
        thread.setDaemon(true);
        return thread;
    });
    private final AtomicBoolean reloadPending = new AtomicBoolean(false);
    private final Thread watcherThread;
    private volatile boolean running = true;

    public McsPackWatcher(McsWorldPackManager packManager, McsServerAccess serverAccess) throws IOException {
        this.packManager = packManager;
        this.serverAccess = serverAccess;
        this.watchService = packManager.mcsRoot().getFileSystem().newWatchService();
        registerRecursively(packManager.mcsRoot());
        this.watcherThread = new Thread(this::watchLoop, "mcs-pack-watcher");
        this.watcherThread.setDaemon(true);
    }

    public void start() {
        watcherThread.start();
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
                if (event.kind() == StandardWatchEventKinds.ENTRY_CREATE && Files.isDirectory(changed)) {
                    try {
                        registerRecursively(changed);
                    } catch (IOException error) {
                        System.out.println("[Minecraft Script] Could not watch " + changed + ": " + error.getMessage());
                    }
                }

                Optional<Path> packFolder = McsPaths.packFolderForChangedPath(packManager.mcsRoot(), changed);
                packFolder.ifPresent(this::schedulePackRefresh);
            }

            if (!key.reset()) {
                keys.remove(key);
            }
        }
    }

    private void scheduleFullScan() {
        executor.schedule(() -> {
            if (packManager.compileAll()) {
                scheduleReload();
            }
        }, COMPILE_DEBOUNCE_MILLIS, TimeUnit.MILLISECONDS);
    }

    private void schedulePackRefresh(Path packFolder) {
        Path normalized = packFolder.toAbsolutePath().normalize();
        ScheduledFuture<?> existing = pendingCompiles.remove(normalized);
        if (existing != null) {
            existing.cancel(false);
        }

        ScheduledFuture<?> future = executor.schedule(() -> {
            pendingCompiles.remove(normalized);
            if (packManager.refreshPack(normalized)) {
                scheduleReload();
            }
        }, COMPILE_DEBOUNCE_MILLIS, TimeUnit.MILLISECONDS);
        pendingCompiles.put(normalized, future);
    }

    private void scheduleReload() {
        if (!reloadPending.compareAndSet(false, true)) {
            return;
        }
        executor.schedule(() -> {
            reloadPending.set(false);
            serverAccess.executeReload();
        }, RELOAD_DEBOUNCE_MILLIS, TimeUnit.MILLISECONDS);
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
        executor.shutdownNow();
        watchService.close();
    }
}
