package dev.spyc0der77.mcspacks.util;

import dev.spyc0der77.mcspacks.toolchain.Diagnostic;
import java.util.List;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;

public final class PlayerFeedback {
    private PlayerFeedback() {
    }

    public static void broadcast(MinecraftServer server, String message) {
        server.submit(() -> {
            Component component = Component.literal(message);
            server.getPlayerList().broadcastSystemMessage(component, false);
        });
    }

    public static void diagnostics(MinecraftServer server, String prefix, List<Diagnostic> diagnostics) {
        for (Diagnostic diagnostic : diagnostics) {
            String location = diagnostic.file() + ":" + diagnostic.line() + ":" + diagnostic.column();
            broadcast(server, prefix + " " + location + " — " + diagnostic.message());
        }
    }
}
