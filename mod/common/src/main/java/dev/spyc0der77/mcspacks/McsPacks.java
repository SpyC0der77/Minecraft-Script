package dev.spyc0der77.mcspacks;

import dev.architectury.event.events.common.LifecycleEvent;
import dev.spyc0der77.mcspacks.config.ModConfig;
import dev.spyc0der77.mcspacks.config.ModConfigManager;
import dev.spyc0der77.mcspacks.pipeline.PackPipeline;
import dev.spyc0der77.mcspacks.registry.PackRegistry;
import dev.spyc0der77.mcspacks.util.McsPaths;
import dev.spyc0der77.mcspacks.util.PlayerFeedback;
import dev.spyc0der77.mcspacks.version.VersionMapper;
import dev.spyc0der77.mcspacks.watch.PackWatcher;
import net.minecraft.server.MinecraftServer;

public final class McsPacks {
    private static PackPipeline pipeline;
    private static PackWatcher watcher;

    private McsPacks() {
    }

    public static void init() {
        McsPaths.ensureLayout();
        ModConfig config = ModConfigManager.load();
        VersionMapper versionMapper = VersionMapper.load();
        PackRegistry registry = new PackRegistry(McsPaths.packsRoot(), McsPaths.compiledRoot());
        pipeline = new PackPipeline(config, versionMapper, registry, PlayerFeedback::broadcast);
        watcher = new PackWatcher(McsPaths.packsRoot(), pipeline::handlePackChange, config.debounceMs);

        pipeline.warmCompileAllPacks();

        LifecycleEvent.SERVER_STARTING.register(McsPacks::onServerStarting);
        LifecycleEvent.SERVER_STARTED.register(McsPacks::onServerStarted);
        LifecycleEvent.SERVER_STOPPING.register(McsPacks::onServerStopping);
    }

    private static void onServerStarting(MinecraftServer server) {
        pipeline.prepareWorldPacks(server);
    }

    private static void onServerStarted(MinecraftServer server) {
        watcher.refreshBaselines();
        watcher.start();
    }

    private static void onServerStopping(MinecraftServer server) {
        watcher.stop();
    }
}
