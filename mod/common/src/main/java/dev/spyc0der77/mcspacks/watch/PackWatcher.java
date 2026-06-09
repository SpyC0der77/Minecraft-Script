package dev.spyc0der77.mcspacks.watch;

import dev.spyc0der77.mcspacks.util.McsPaths;
import java.io.IOException;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardWatchEventKinds;
import java.nio.file.WatchEvent;
import java.nio.file.WatchKey;
import java.nio.file.WatchService;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;

public final class PackWatcher {
    private final Path packsRoot;
    private final Consumer<Path> onPackChange;
    private final long debounceMs;
    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor(runnable -> {
        Thread thread = new Thread(runnable, "mcs-packs-watcher-scheduler");
        thread.setDaemon(true);
        return thread;
    });
    private final Map<Path, ScheduledFuture<?>> pending = new ConcurrentHashMap<>();
    private final Map<Path, Long> lastModified = new ConcurrentHashMap<>();
    private volatile boolean running;
    private Thread watchThread;

    public PackWatcher(Path packsRoot, Consumer<Path> onPackChange, long debounceMs) {
        this.packsRoot = packsRoot;
        this.onPackChange = onPackChange;
        this.debounceMs = Math.max(100, debounceMs);
    }

    public synchronized void start() {
        if (running) {
            return;
        }
        running = true;
        seedModifiedTimes();
        watchThread = new Thread(this::runLoop, "mcs-packs-watcher");
        watchThread.setDaemon(true);
        watchThread.start();
    }

    public void refreshBaselines() {
        seedModifiedTimes();
    }

    public synchronized void stop() {
        running = false;
        if (watchThread != null) {
            watchThread.interrupt();
            watchThread = null;
        }
        pending.values().forEach(future -> future.cancel(false));
        pending.clear();
    }

    private void runLoop() {
        try (WatchService watchService = FileSystems.getDefault().newWatchService()) {
            registerTree(watchService, packsRoot);
            while (running) {
                WatchKey key = watchService.poll(1, TimeUnit.SECONDS);
                if (key == null) {
                    pollEntryFiles();
                    continue;
                }
                Path watchedDirectory = (Path) key.watchable();
                for (WatchEvent<?> event : key.pollEvents()) {
                    if (event.kind() == StandardWatchEventKinds.OVERFLOW) {
                        continue;
                    }
                    Path context = (Path) event.context();
                    if (context == null || shouldIgnore(context)) {
                        continue;
                    }
                    Path changedPath = watchedDirectory.resolve(context);
                    if (event.kind() == StandardWatchEventKinds.ENTRY_CREATE && Files.isDirectory(changedPath)) {
                        registerTree(watchService, changedPath);
                    }
                    Path packFolder = resolvePackFolder(changedPath);
                    if (packFolder != null) {
                        touchEntryTimestamp(packFolder);
                        schedule(packFolder);
                    }
                }
                if (!key.reset()) {
                    registerDirectory(watchService, watchedDirectory);
                }
            }
        } catch (InterruptedException ignored) {
            Thread.currentThread().interrupt();
        } catch (IOException error) {
            throw new IllegalStateException("Failed to watch mcs_packs", error);
        }
    }

    private void schedule(Path packFolder) {
        pending.compute(packFolder, (path, existing) -> {
            if (existing != null) {
                existing.cancel(false);
            }
            return scheduler.schedule(() -> {
                pending.remove(path);
                onPackChange.accept(path);
            }, debounceMs, TimeUnit.MILLISECONDS);
        });
    }

    private void seedModifiedTimes() {
        try {
            if (!Files.exists(packsRoot)) {
                return;
            }
            try (var stream = Files.list(packsRoot)) {
                for (Path packFolder : stream.toList()) {
                    if (!isPackFolder(packFolder)) {
                        continue;
                    }
                    Path entry = packFolder.resolve(McsPaths.DEFAULT_ENTRY);
                    if (Files.exists(entry)) {
                        lastModified.put(entry, Files.getLastModifiedTime(entry).toMillis());
                    }
                }
            }
        } catch (IOException ignored) {
            // Best-effort baseline for polling.
        }
    }

    private void pollEntryFiles() {
        try {
            if (!Files.exists(packsRoot)) {
                return;
            }
            try (var stream = Files.list(packsRoot)) {
                for (Path packFolder : stream.toList()) {
                    if (!isPackFolder(packFolder)) {
                        continue;
                    }
                    Path entry = packFolder.resolve(McsPaths.DEFAULT_ENTRY);
                    if (!Files.exists(entry)) {
                        continue;
                    }
                    long modified = Files.getLastModifiedTime(entry).toMillis();
                    Long previous = lastModified.put(entry, modified);
                    if (previous == null || modified > previous) {
                        schedule(packFolder);
                    }
                }
            }
        } catch (IOException ignored) {
            // Polling is a fallback when native watch events are missed.
        }
    }

    private void touchEntryTimestamp(Path packFolder) {
        try {
            Path entry = packFolder.resolve(McsPaths.DEFAULT_ENTRY);
            if (Files.exists(entry)) {
                lastModified.put(entry, Files.getLastModifiedTime(entry).toMillis());
            }
        } catch (IOException ignored) {
            // Ignore timestamp refresh failures.
        }
    }

    private Path resolvePackFolder(Path changedPath) {
        if (!changedPath.startsWith(packsRoot)) {
            return null;
        }

        Path current;
        if (Files.isDirectory(changedPath)) {
            current = changedPath;
        } else {
            String fileName = changedPath.getFileName().toString().toLowerCase(Locale.ROOT);
            if (!fileName.endsWith(".mcs")) {
                return null;
            }
            current = changedPath.getParent();
        }

        while (current != null && current.startsWith(packsRoot) && !packsRoot.equals(current)) {
            if (isPackFolder(current)) {
                Path entry = current.resolve(McsPaths.DEFAULT_ENTRY);
                return Files.exists(entry) ? current : null;
            }
            current = current.getParent();
        }
        return null;
    }

    private boolean isPackFolder(Path packFolder) {
        if (!Files.isDirectory(packFolder) || !packFolder.startsWith(packsRoot)) {
            return false;
        }
        if (packsRoot.equals(packFolder)) {
            return false;
        }
        Path relative = packsRoot.relativize(packFolder);
        if (relative.getNameCount() != 1) {
            return false;
        }
        String name = packFolder.getFileName().toString();
        return !name.startsWith("_") && !name.startsWith(".");
    }

    private static boolean shouldIgnore(Path path) {
        String name = path.getFileName().toString();
        return name.startsWith(".") || name.endsWith("~") || name.endsWith(".swp") || name.endsWith(".tmp");
    }

    private static void registerTree(WatchService watchService, Path root) throws IOException {
        if (!Files.exists(root)) {
            Files.createDirectories(root);
        }
        try (var stream = Files.walk(root)) {
            stream.filter(Files::isDirectory).forEach(dir -> registerDirectory(watchService, dir));
        }
    }

    private static void registerDirectory(WatchService watchService, Path directory) {
        String name = directory.getFileName() == null ? "" : directory.getFileName().toString();
        if (name.equals("_compiled")) {
            return;
        }
        try {
            if (isWindows()) {
                directory.register(
                        watchService,
                        new WatchEvent.Kind[]{
                                StandardWatchEventKinds.ENTRY_CREATE,
                                StandardWatchEventKinds.ENTRY_MODIFY,
                                StandardWatchEventKinds.ENTRY_DELETE
                        },
                        com.sun.nio.file.SensitivityWatchEventModifier.HIGH
                );
            } else {
                directory.register(
                        watchService,
                        StandardWatchEventKinds.ENTRY_CREATE,
                        StandardWatchEventKinds.ENTRY_MODIFY,
                        StandardWatchEventKinds.ENTRY_DELETE
                );
            }
        } catch (IOException ignored) {
            // Some directories may not be watchable on all platforms.
        }
    }

    private static boolean isWindows() {
        String os = System.getProperty("os.name", "");
        return os.toLowerCase(Locale.ROOT).contains("win");
    }
}
