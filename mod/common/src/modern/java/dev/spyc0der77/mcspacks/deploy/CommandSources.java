package dev.spyc0der77.mcspacks.deploy;

import net.minecraft.commands.CommandSourceStack;
import net.minecraft.server.permissions.PermissionSet;

public final class CommandSources {
    private CommandSources() {
    }

    public static CommandSourceStack withAllPermissions(CommandSourceStack source) {
        return source.withPermission(PermissionSet.ALL_PERMISSIONS);
    }
}
