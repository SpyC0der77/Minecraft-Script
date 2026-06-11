package dev.spyc0der.minecraftscript;

import java.io.IOException;
import java.nio.file.Path;

public final class McsModRuntime {
    private static McsPackWatcher activeWatcher;
    private static McsWorldPackManager activePackManager;
    private static McsServerAccess activeServerAccess;

    private McsModRuntime() {
    }

    public static synchronized void serverStarted(McsServerAccess serverAccess) {
        serverStopping();

        try {
            Path configDirectory = McsPaths.configDirectory(serverAccess.serverDirectory());
            McsModConfig config = McsModConfig.load(configDirectory);
            McsWorldPackManager packManager = new McsWorldPackManager(
                    serverAccess,
                    new ProcessMcsCompiler(config),
                    config
            );
            packManager.initializeWorldFolders();
            packManager.compileAll();
            activePackManager = packManager;
            activeServerAccess = serverAccess;
            applyHotReloadState(packManager.config().hotReload());
            serverAccess.executeStartupReload();
        } catch (IOException error) {
            String message = "Could not initialize mcs_packs: " + error.getMessage();
            System.out.println("[Minecraft Script] " + message);
            serverAccess.notifyOperators(message);
        }
    }

    public static synchronized void serverStopping() {
        stopWatcher();
        activePackManager = null;
        activeServerAccess = null;
    }

    public static synchronized McsWorldPackManager packManager() {
        return activePackManager;
    }

    public static synchronized McsServerAccess serverAccess() {
        return activeServerAccess;
    }

    public static synchronized void applyHotReloadState(boolean enabled) {
        if (activePackManager == null || activeServerAccess == null) {
            return;
        }

        if (enabled) {
            startWatcher();
            return;
        }
        stopWatcher();
    }

    private static void startWatcher() {
        if (activeWatcher != null || activePackManager == null || activeServerAccess == null) {
            return;
        }
        try {
            activeWatcher = new McsPackWatcher(activePackManager, activeServerAccess);
            activeWatcher.start();
        } catch (IOException error) {
            String message = "Could not start MCS hot reload watcher: " + error.getMessage();
            System.out.println("[Minecraft Script] " + message);
            activeServerAccess.notifyOperators(message);
        }
    }

    private static void stopWatcher() {
        if (activeWatcher == null) {
            return;
        }
        try {
            activeWatcher.close();
        } catch (IOException ignored) {
        }
        activeWatcher = null;
    }
}
