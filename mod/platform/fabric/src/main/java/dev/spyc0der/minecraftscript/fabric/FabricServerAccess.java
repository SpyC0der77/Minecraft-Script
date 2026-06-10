package dev.spyc0der.minecraftscript.fabric;

import dev.spyc0der.minecraftscript.McsBuildInfo;
import dev.spyc0der.minecraftscript.McsServerAccess;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.storage.LevelResource;

import java.nio.file.Path;

final class FabricServerAccess implements McsServerAccess {
    private final MinecraftServer server;

    FabricServerAccess(MinecraftServer server) {
        this.server = server;
    }

    @Override
    public Path saveRoot() {
        return server.getWorldPath(LevelResource.ROOT);
    }

    @Override
    public String minecraftVersion() {
        return McsBuildInfo.MINECRAFT_VERSION;
    }

    @Override
    public void executeReload() {
        server.execute(() -> {
            CommandSourceStack source = server.createCommandSourceStack()
                    .withPermission(4)
                    .withSuppressedOutput();
            server.getCommands().performPrefixedCommand(source, "reload");
        });
    }

    @Override
    public void notifyOperators(String message) {
        server.execute(() -> server.getPlayerList().getPlayers().forEach(player -> {
            if (server.getPlayerList().isOp(player.getGameProfile())) {
                player.sendSystemMessage(Component.literal("[MCS] " + message).withStyle(ChatFormatting.YELLOW));
            }
        }));
    }
}
