package dev.spyc0der.minecraftscript.forge;

import dev.spyc0der.minecraftscript.McsModRuntime;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;
import net.minecraftforge.fml.common.Mod;

@Mod("minecraft_script")
public final class McsForgeMod {
    public McsForgeMod() {
        ServerStartedEvent.BUS.addListener(this::onServerStarted);
        ServerStoppingEvent.BUS.addListener(this::onServerStopping);
    }

    private void onServerStarted(ServerStartedEvent event) {
        McsModRuntime.serverStarted(new ForgeServerAccess(event.getServer()));
    }

    private void onServerStopping(ServerStoppingEvent event) {
        McsModRuntime.serverStopping();
    }
}
