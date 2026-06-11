package dev.spyc0der.minecraftscript.fabric;

import dev.spyc0der.minecraftscript.McsModRuntime;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;

public final class McsFabricMod implements ModInitializer {
    @Override
    public void onInitialize() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registry, environment) ->
                McsFabricCommands.register(dispatcher));
        ServerLifecycleEvents.SERVER_STARTED.register(server ->
                McsModRuntime.serverStarted(new FabricServerAccess(server)));
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> McsModRuntime.serverStopping());
    }
}
