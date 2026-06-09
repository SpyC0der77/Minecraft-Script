package dev.spyc0der77.mcspacks.pipeline;

import dev.architectury.platform.Platform;
import dev.spyc0der77.mcspacks.config.ModConfig;
import dev.spyc0der77.mcspacks.deploy.DatapackDeployer;
import dev.spyc0der77.mcspacks.registry.PackDefinition;
import dev.spyc0der77.mcspacks.registry.PackRegistry;
import dev.spyc0der77.mcspacks.toolchain.Diagnostic;
import dev.spyc0der77.mcspacks.toolchain.McsToolchain;
import dev.spyc0der77.mcspacks.util.PlayerFeedback;
import dev.spyc0der77.mcspacks.version.VersionMapper;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.BiConsumer;
import net.minecraft.server.MinecraftServer;

public final class PackPipeline {
    private final ModConfig config;
    private final VersionMapper versionMapper;
    private final PackRegistry registry;
    private final BiConsumer<MinecraftServer, String> messenger;
    private final ExecutorService executor = Executors.newSingleThreadExecutor(runnable -> {
        Thread thread = new Thread(runnable, "mcs-packs-pipeline");
        thread.setDaemon(true);
        return thread;
    });
    private final Map<String, Long> generations = new ConcurrentHashMap<>();
    private volatile MinecraftServer activeServer;

    public PackPipeline(
            ModConfig config,
            VersionMapper versionMapper,
            PackRegistry registry,
            BiConsumer<MinecraftServer, String> messenger
    ) {
        this.config = config;
        this.versionMapper = versionMapper;
        this.registry = registry;
        this.messenger = messenger;
    }

    public void bindServer(MinecraftServer server) {
        this.activeServer = server;
    }

    public void warmCompileAllPacks() {
        executor.submit(() -> {
            try {
                for (PackDefinition pack : registry.discover()) {
                    runToolchain(pack, 0L);
                }
            } catch (IOException ignored) {
                // Warm compile is best-effort before a world is opened.
            }
        });
    }

    public void prepareWorldPacks(MinecraftServer server) {
        bindServer(server);
        try {
            for (PackDefinition pack : registry.discover()) {
                processPack(server, pack, false);
            }
        } catch (IOException error) {
            messenger.accept(server, "[MCS] Failed to prepare packs: " + error.getMessage());
        }
    }

    public void handlePackChange(Path packFolder) {
        MinecraftServer server = activeServer;
        if (server == null) {
            return;
        }
        executor.submit(() -> {
            try {
                PackDefinition pack = registry.resolvePack(packFolder);
                if (pack == null) {
                    return;
                }
                processPack(server, pack, true);
            } catch (Exception error) {
                messenger.accept(server, "[MCS] Failed to process " + packFolder.getFileName() + ": " + error.getMessage());
            }
        });
    }

    private void processPack(MinecraftServer server, PackDefinition pack, boolean reloadAfterDeploy) {
        long generation = generations.merge(pack.id(), 1L, Long::sum);
        messenger.accept(server, "[MCS] Processing " + pack.id() + "…");
        if (!runToolchain(pack, generation)) {
            return;
        }
        if (!Files.exists(pack.compiledFolder())) {
            messenger.accept(server, "[MCS] Compile finished but output folder is missing for " + pack.id());
            return;
        }

        try {
            if (config.autoReload) {
                DatapackDeployer.syncPack(server, pack.compiledFolder(), pack.displayName());
                if (reloadAfterDeploy) {
                    DatapackDeployer.reload(server);
                    messenger.accept(server, "[MCS] Reloaded " + pack.id());
                } else {
                    messenger.accept(server, "[MCS] Prepared " + pack.id());
                }
            } else {
                messenger.accept(server, "[MCS] Built " + pack.id() + " (autoReload disabled)");
            }
        } catch (Exception error) {
            messenger.accept(server, "[MCS] Failed to deploy " + pack.id() + ": " + error.getMessage());
        }
    }

    private boolean runToolchain(PackDefinition pack, long generation) {
        String mcsProfile = versionMapper.resolveMcsProfile(Platform.getMinecraftVersion(), config.minecraftVersion);
        McsToolchain toolchain = new McsToolchain(config, mcsProfile);

        List<Diagnostic> lintDiagnostics = toolchain.lint(pack);
        if (!lintDiagnostics.isEmpty()) {
            MinecraftServer server = activeServer;
            if (server != null) {
                PlayerFeedback.diagnostics(server, "[MCS]", lintDiagnostics);
            }
            if (config.blockCompileOnLintErrors && lintDiagnostics.stream().anyMatch(Diagnostic::isError)) {
                return false;
            }
        }
        if (generation != 0L && generation != generations.get(pack.id())) {
            return false;
        }

        List<Diagnostic> compileDiagnostics = toolchain.compile(pack);
        if (!compileDiagnostics.isEmpty()) {
            MinecraftServer server = activeServer;
            if (server != null) {
                PlayerFeedback.diagnostics(server, "[MCS]", compileDiagnostics);
            }
            return false;
        }
        if (generation != 0L && generation != generations.get(pack.id())) {
            return false;
        }

        List<Diagnostic> spyglassDiagnostics = toolchain.validateWithSpyglass(pack, Platform.getMinecraftVersion());
        if (!spyglassDiagnostics.isEmpty()) {
            MinecraftServer server = activeServer;
            if (server != null) {
                PlayerFeedback.diagnostics(server, "[Spyglass]", spyglassDiagnostics);
            }
            if (config.blockReloadOnSpyglassErrors && spyglassDiagnostics.stream().anyMatch(Diagnostic::isError)) {
                return false;
            }
        }
        return generation == 0L || generation == generations.get(pack.id());
    }
}
