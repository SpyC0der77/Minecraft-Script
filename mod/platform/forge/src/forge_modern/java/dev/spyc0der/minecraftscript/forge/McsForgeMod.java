package dev.spyc0der.minecraftscript.forge;

import dev.spyc0der.minecraftscript.McsModRuntime;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;
import net.minecraftforge.fml.common.Mod;

@Mod("minecraft_script")
public final class McsForgeMod {
    public McsForgeMod() {
        RegisterCommandsEvent.BUS.addListener(this::onRegisterCommands);
        ServerStartedEvent.BUS.addListener(this::onServerStarted);
        ServerStoppingEvent.BUS.addListener(this::onServerStopping);
    }

    private void onRegisterCommands(RegisterCommandsEvent event) {
        McsForgeCommands.register(event.getDispatcher());
    }

    private void onServerStarted(ServerStartedEvent event) {
        McsModRuntime.serverStarted(new ForgeServerAccess(event.getServer()));
    }

    private void onServerStopping(ServerStoppingEvent event) {
        McsModRuntime.serverStopping();
    }
}
