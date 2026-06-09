package dev.spyc0der77.mcspacks.deploy;

import net.minecraft.commands.CommandSourceStack;

public final class CommandSources {
    private static final int ALL_PERMISSIONS = 4;

    private CommandSources() {
    }

    public static CommandSourceStack withAllPermissions(CommandSourceStack source) {
        return source.withPermission(ALL_PERMISSIONS);
    }
}
