package dev.spyc0der.minecraftscript.neoforge;

import dev.spyc0der.minecraftscript.McsModRuntime;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.server.ServerStoppingEvent;

@Mod("minecraft_script")
public final class McsNeoForgeMod {
    public McsNeoForgeMod() {
        NeoForge.EVENT_BUS.register(this);
    }

    @SubscribeEvent
    public void onServerStarted(ServerStartedEvent event) {
        McsModRuntime.serverStarted(new NeoForgeServerAccess(event.getServer()));
    }

    @SubscribeEvent
    public void onServerStopping(ServerStoppingEvent event) {
        McsModRuntime.serverStopping();
    }
}
