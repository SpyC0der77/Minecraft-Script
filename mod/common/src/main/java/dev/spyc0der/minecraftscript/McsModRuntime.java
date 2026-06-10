package dev.spyc0der.minecraftscript;

import java.io.IOException;

public final class McsModRuntime {
    private static McsPackWatcher activeWatcher;

    private McsModRuntime() {
    }

    public static synchronized void serverStarted(McsServerAccess serverAccess) {
        serverStopping();

        try {
            McsWorldPackManager packManager = new McsWorldPackManager(
                    serverAccess,
                    new ProcessMcsCompiler(McsCompilerConfig.load(McsPaths.mcsPacksRoot(serverAccess.saveRoot())))
            );
            packManager.initializeWorldFolders();
            if (packManager.compileAll()) {
                serverAccess.executeReload();
            }
            activeWatcher = new McsPackWatcher(packManager, serverAccess);
            activeWatcher.start();
        } catch (IOException error) {
            String message = "Could not initialize mcs_packs: " + error.getMessage();
            System.out.println("[Minecraft Script] " + message);
            serverAccess.notifyOperators(message);
        }
    }

    public static synchronized void serverStopping() {
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
