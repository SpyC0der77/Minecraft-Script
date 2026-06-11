package dev.spyc0der.minecraftscript.fabric;

import dev.spyc0der.minecraftscript.McsBuildInfo;
import dev.spyc0der.minecraftscript.McsServerAccess;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.permissions.LevelBasedPermissionSet;
import net.minecraft.server.players.NameAndId;
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
    public Path serverDirectory() {
        return server.getServerDirectory();
    }

    @Override
    public String minecraftVersion() {
        return McsBuildInfo.MINECRAFT_VERSION;
    }

    @Override
    public void executeReload() {
        runOnServerThread(this::performReload);
    }

    @Override
    public void executeStartupReload() {
        runOnServerThread(this::performReload);
    }

    private void performReload() {
        CommandSourceStack source = server.createCommandSourceStack()
                .withPermission(LevelBasedPermissionSet.ADMIN)
                .withSuppressedOutput();
        server.getCommands().performPrefixedCommand(source, "reload");
    }

    private void runOnServerThread(Runnable action) {
        if (server.isSameThread()) {
            action.run();
        } else {
            server.execute(action);
        }
    }

    @Override
    public void notifyOperators(String message) {
        server.execute(() -> server.getPlayerList().getPlayers().forEach(player -> {
            if (server.getPlayerList().isOp(new NameAndId(player.getGameProfile()))) {
                player.sendSystemMessage(Component.literal("[MCS] " + message).withStyle(ChatFormatting.YELLOW));
            }
        }));
    }
}
