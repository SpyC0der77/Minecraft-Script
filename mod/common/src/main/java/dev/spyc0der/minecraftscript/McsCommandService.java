package dev.spyc0der.minecraftscript;

import java.io.IOException;
import java.util.List;

public final class McsCommandService {
    private McsCommandService() {
    }

    public static List<String> packNameSuggestions() {
        McsWorldPackManager packManager = McsModRuntime.packManager();
        if (packManager == null) {
            return List.of();
        }
        try {
            return packManager.discoverPackNames();
        } catch (IOException error) {
            return List.of();
        }
    }

    public static McsCommandResult setHotReloading(boolean enabled, String packName) {
        McsWorldPackManager packManager = McsModRuntime.packManager();
        if (packManager == null) {
            return McsCommandResult.error("Minecraft Script is not active on this server.");
        }
        try {
            McsCommandResult result = packManager.setHotReloading(enabled, packName);
            if (result.success() && (packName == null || packName.isBlank())) {
                McsModRuntime.applyHotReloadState(enabled);
            }
            return result;
        } catch (IOException error) {
            return McsCommandResult.error("Could not save MCS config: " + error.getMessage());
        }
    }

    public static McsCommandResult setPackEnabled(String packName, boolean enabled) {
        McsWorldPackManager packManager = McsModRuntime.packManager();
        McsServerAccess serverAccess = McsModRuntime.serverAccess();
        if (packManager == null || serverAccess == null) {
            return McsCommandResult.error("Minecraft Script is not active on this server.");
        }
        try {
            McsCommandResult result = packManager.setPackEnabled(packName, enabled);
            if (result.success()) {
                serverAccess.executeReload();
            }
            return result;
        } catch (IOException error) {
            return McsCommandResult.error("Could not update pack state: " + error.getMessage());
        }
    }

    public static McsCommandResult listPacks() {
        McsWorldPackManager packManager = McsModRuntime.packManager();
        if (packManager == null) {
            return McsCommandResult.error("Minecraft Script is not active on this server.");
        }
        try {
            return packManager.listPacks();
        } catch (IOException error) {
            return McsCommandResult.error("Could not list MCS packs: " + error.getMessage());
        }
    }

    public static McsCommandResult createPack(String packName, String scope) {
        McsWorldPackManager packManager = McsModRuntime.packManager();
        McsServerAccess serverAccess = McsModRuntime.serverAccess();
        if (packManager == null || serverAccess == null) {
            return McsCommandResult.error("Minecraft Script is not active on this server.");
        }
        McsPackSource source = parsePackScope(scope);
        if (source == null) {
            return McsCommandResult.error("Scope must be 'global' or 'local'.");
        }
        try {
            McsCommandResult result = packManager.createPack(packName, source);
            if (result.success()) {
                serverAccess.executeReload();
            }
            return result;
        } catch (IOException error) {
            return McsCommandResult.error("Could not create MCS pack: " + error.getMessage());
        }
    }

    private static McsPackSource parsePackScope(String scope) {
        if (scope == null) {
            return null;
        }
        return switch (scope.trim().toLowerCase()) {
            case "global" -> McsPackSource.GLOBAL;
            case "local" -> McsPackSource.WORLD;
            default -> null;
        };
    }

    public static McsCommandResult reload(String packName) {
        McsWorldPackManager packManager = McsModRuntime.packManager();
        McsServerAccess serverAccess = McsModRuntime.serverAccess();
        if (packManager == null || serverAccess == null) {
            return McsCommandResult.error("Minecraft Script is not active on this server.");
        }
        try {
            McsCommandResult result = packManager.reload(packName);
            if (result.success()) {
                serverAccess.executeReload();
            }
            return result;
        } catch (IOException error) {
            return McsCommandResult.error("Could not reload MCS packs: " + error.getMessage());
        }
    }
}
