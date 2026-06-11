package dev.spyc0der.minecraftscript;

import java.io.IOException;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

public final class McsWorldPackManager {
    private final Path saveRoot;
    private final Path worldMcsRoot;
    private final Path globalMcsRoot;
    private final Path datapacksRoot;
    private final Path configDirectory;
    private final String minecraftVersion;
    private final McsCompiler compiler;
    private final McsServerAccess serverAccess;
    private McsModConfig config;

    public McsWorldPackManager(McsServerAccess serverAccess, McsCompiler compiler, McsModConfig config) {
        this.serverAccess = Objects.requireNonNull(serverAccess, "serverAccess");
        this.compiler = Objects.requireNonNull(compiler, "compiler");
        this.config = Objects.requireNonNull(config, "config");
        this.saveRoot = serverAccess.saveRoot();
        this.worldMcsRoot = McsPaths.worldMcsPacksRoot(saveRoot);
        this.globalMcsRoot = McsPaths.globalMcsPacksRoot(serverAccess.serverDirectory());
        this.datapacksRoot = McsPaths.datapacksRoot(saveRoot);
        this.configDirectory = McsPaths.configDirectory(serverAccess.serverDirectory());
        this.minecraftVersion = serverAccess.minecraftVersion();
    }

    public Path worldMcsRoot() {
        return worldMcsRoot;
    }

    public Path globalMcsRoot() {
        return globalMcsRoot;
    }

    public Path mcsRoot() {
        return worldMcsRoot;
    }

    public List<Path> watchedMcsRoots() {
        return List.of(worldMcsRoot, globalMcsRoot);
    }

    public McsModConfig config() {
        return config;
    }

    public Path configDirectory() {
        return configDirectory;
    }

    public void initializeWorldFolders() throws IOException {
        Files.createDirectories(worldMcsRoot);
        Files.createDirectories(globalMcsRoot);
        Files.createDirectories(datapacksRoot);

        Path starterPack = globalMcsRoot.resolve(McsStarterPack.STARTER_NAME).resolve(McsPaths.PACK_FILE);
        if (!Files.exists(starterPack)) {
            Files.createDirectories(starterPack.getParent());
            Files.writeString(starterPack, McsStarterPack.STARTER_SOURCE);
        }
    }

    public McsCommandResult createPack(String packName, McsPackSource source) throws IOException {
        String trimmedName = packName == null ? "" : packName.trim();
        if (!McsStarterPack.isValidPackName(trimmedName)) {
            return McsCommandResult.error("Invalid pack name '" + trimmedName + "'.");
        }
        if (findPackEntry(trimmedName).isPresent()) {
            return McsCommandResult.error("Pack '" + trimmedName + "' already exists.");
        }

        Path root = source == McsPackSource.GLOBAL ? globalMcsRoot : worldMcsRoot;
        Path packFolder = root.resolve(trimmedName);
        Path packFile = packFolder.resolve(McsPaths.PACK_FILE);
        Files.createDirectories(packFolder);
        Files.writeString(packFile, McsStarterPack.packSource(trimmedName));

        McsPackEntry entry = new McsPackEntry(packFolder, source);
        boolean compiled = refreshPackEntry(entry);
        return McsCommandResult.ok(
                "Created " + sourceLabel(source) + " pack '" + trimmedName + "' at "
                        + packFolder
                        + (compiled ? " and compiled it." : ".")
        );
    }

    public List<McsPackEntry> discoverPackEntries() throws IOException {
        Map<String, McsPackEntry> packsByKey = new LinkedHashMap<>();

        for (Path packFolder : listPackFolders(globalMcsRoot)) {
            packsByKey.putIfAbsent(
                    McsPaths.packKey(packFolder.getFileName().toString()),
                    new McsPackEntry(packFolder, McsPackSource.GLOBAL)
            );
        }
        for (Path packFolder : listPackFolders(worldMcsRoot)) {
            packsByKey.put(
                    McsPaths.packKey(packFolder.getFileName().toString()),
                    new McsPackEntry(packFolder, McsPackSource.WORLD)
            );
        }

        return List.copyOf(packsByKey.values());
    }

    public List<Path> discoverPackFolders() throws IOException {
        return discoverPackEntries().stream().map(McsPackEntry::packFolder).toList();
    }

    public List<String> discoverPackNames() throws IOException {
        return discoverPackEntries().stream().map(McsPackEntry::packName).toList();
    }

    public Optional<McsPackEntry> findPackEntry(String packName) throws IOException {
        String packKey = McsPaths.packKey(packName);
        return discoverPackEntries().stream()
                .filter(entry -> McsPaths.packKey(entry.packName()).equals(packKey))
                .findFirst();
    }

    public boolean isPackEnabled(McsPackEntry entry) {
        return config.isPackEnabled(entry.packName());
    }

    public boolean isHotReloadEnabledForPack(McsPackEntry entry) {
        return config.isHotReloadEnabledForPack(entry.packName());
    }

    public boolean compileAll() {
        boolean changed = false;
        try {
            for (McsPackEntry entry : discoverPackEntries()) {
                changed |= refreshPackEntry(entry);
            }
        } catch (IOException error) {
            report("Could not scan mcs_packs: " + error.getMessage());
        }
        return changed;
    }

    public void notifyPackChangePending(Path packFolder) {
        report("Detected changes in " + packFolder.getFileName() + ", recompiling...");
    }

    public boolean refreshPack(Path packFolder) {
        try {
            Optional<McsPackEntry> entry = findPackEntry(packFolder.getFileName().toString());
            if (entry.isEmpty()) {
                return deleteGeneratedPack(packFolder, resolvePackSource(packFolder));
            }
            return refreshPackEntry(entry.get());
        } catch (IOException error) {
            report("Could not refresh " + packFolder.getFileName() + ": " + error.getMessage());
            return false;
        }
    }

    public boolean refreshPackEntry(McsPackEntry entry) {
        Path packFile = entry.packFolder().resolve(McsPaths.PACK_FILE);
        if (!config.isPackEnabled(entry.packName())) {
            return deleteGeneratedPack(entry.packFolder(), entry.source());
        }
        if (Files.isRegularFile(packFile)) {
            return compilePack(entry);
        }
        return deleteGeneratedPack(entry.packFolder(), entry.source());
    }

    public boolean compilePack(McsPackEntry entry) {
        if (!config.isPackEnabled(entry.packName())) {
            return false;
        }
        return compilePack(entry.packFolder(), entry.source());
    }

    public boolean compilePack(Path packFolder) {
        return compilePack(packFolder, resolvePackSource(packFolder));
    }

    public boolean compilePack(Path packFolder, McsPackSource source) {
        if (!config.isPackEnabled(packFolder.getFileName().toString())) {
            return false;
        }
        String datapackName = McsPaths.generatedDatapackName(packFolder, source);
        Path temporaryRoot = null;
        try {
            temporaryRoot = Files.createTempDirectory(datapacksRoot, "." + datapackName + "-compile-");
            McsCompileResult result = compiler.compile(
                    packFolder.resolve(McsPaths.PACK_FILE),
                    datapackName,
                    temporaryRoot,
                    minecraftVersion
            );
            if (!result.succeeded()) {
                report("Failed to compile " + packFolder.getFileName() + ":\n" + result.output());
                return false;
            }

            Path compiledDatapack = temporaryRoot.resolve(datapackName);
            if (!Files.isDirectory(compiledDatapack)) {
                report("Compiler finished without creating " + compiledDatapack);
                return false;
            }

            replaceGeneratedDatapack(compiledDatapack, datapacksRoot.resolve(datapackName));
            report("Compiled MCS pack " + packFolder.getFileName() + " (" + sourceLabel(source) + ") for Minecraft "
                    + minecraftVersion);
            return true;
        } catch (IOException error) {
            report("Could not compile " + packFolder.getFileName() + ": " + error.getMessage());
            return false;
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            report("Compile interrupted for " + packFolder.getFileName());
            return false;
        } finally {
            if (temporaryRoot != null) {
                try {
                    deleteRecursively(temporaryRoot);
                } catch (IOException ignored) {
                }
            }
        }
    }

    public boolean deleteGeneratedPack(Path packFolder) {
        return deleteGeneratedPack(packFolder, resolvePackSource(packFolder));
    }

    public boolean deleteGeneratedPack(Path packFolder, McsPackSource source) {
        Path target = datapacksRoot.resolve(McsPaths.generatedDatapackName(packFolder, source));
        if (!Files.exists(target)) {
            return false;
        }
        try {
            deleteRecursively(target);
            report("Removed generated datapack " + target.getFileName());
            return true;
        } catch (IOException error) {
            report("Could not remove generated datapack " + target.getFileName() + ": " + error.getMessage());
            return false;
        }
    }

    public McsCommandResult setHotReloading(boolean enabled, String packName) throws IOException {
        if (packName == null || packName.isBlank()) {
            if (config.hotReload() == enabled) {
                return McsCommandResult.ok("Hot reloading is already " + (enabled ? "enabled" : "disabled") + ".");
            }
            config = config.withHotReload(enabled);
            config.save(configDirectory);
            return McsCommandResult.ok("Hot reloading " + (enabled ? "enabled" : "disabled") + " globally.");
        }

        Optional<McsPackEntry> entry = findPackEntry(packName);
        if (entry.isEmpty()) {
            return McsCommandResult.error("Unknown MCS pack '" + packName + "'.");
        }

        boolean currentlyEnabled = config.isHotReloadEnabledForPack(entry.get().packName());
        if (currentlyEnabled == enabled) {
            return McsCommandResult.ok(
                    "Hot reloading for pack '" + entry.get().packName() + "' is already "
                            + (enabled ? "enabled" : "disabled") + "."
            );
        }

        config = config.withHotReloadForPack(entry.get().packName(), enabled);
        config.save(configDirectory);
        return McsCommandResult.ok(
                "Hot reloading for pack '" + entry.get().packName() + "' "
                        + (enabled ? "enabled" : "disabled") + "."
        );
    }

    public McsCommandResult setPackEnabled(String packName, boolean enabled) throws IOException {
        if (packName == null || packName.isBlank()) {
            List<McsPackEntry> entries = discoverPackEntries();
            if (entries.isEmpty()) {
                return McsCommandResult.error("No MCS packs found.");
            }

            boolean changed = false;
            for (McsPackEntry entry : entries) {
                if (config.isPackEnabled(entry.packName()) != enabled) {
                    config = config.withPackEnabled(entry.packName(), enabled);
                    changed = true;
                }
            }
            if (!changed) {
                return McsCommandResult.ok("All MCS packs are already " + (enabled ? "enabled" : "disabled") + ".");
            }
            config.save(configDirectory);

            boolean datapacksChanged = false;
            for (McsPackEntry entry : entries) {
                datapacksChanged |= refreshPackEntry(entry);
            }
            return McsCommandResult.ok(
                    "All MCS packs " + (enabled ? "enabled" : "disabled")
                            + (datapacksChanged ? " and datapacks were updated." : ".")
            );
        }

        Optional<McsPackEntry> entry = findPackEntry(packName);
        if (entry.isEmpty()) {
            return McsCommandResult.error("Unknown MCS pack '" + packName + "'.");
        }

        boolean currentlyEnabled = config.isPackEnabled(entry.get().packName());
        if (currentlyEnabled == enabled) {
            return McsCommandResult.ok(
                    "Pack '" + entry.get().packName() + "' is already " + (enabled ? "enabled" : "disabled") + "."
            );
        }

        config = config.withPackEnabled(entry.get().packName(), enabled);
        config.save(configDirectory);

        boolean changed = refreshPackEntry(entry.get());
        return McsCommandResult.ok(
                "Pack '" + entry.get().packName() + "' (" + sourceLabel(entry.get().source()) + ") "
                        + (enabled ? "enabled" : "disabled")
                        + (changed ? " and datapacks were updated." : ".")
        );
    }

    public McsCommandResult reload(String packName) throws IOException {
        if (packName == null || packName.isBlank()) {
            boolean changed = compileAll();
            return McsCommandResult.ok(
                    changed ? "Recompiled enabled MCS packs." : "No enabled MCS pack changes were needed."
            );
        }

        Optional<McsPackEntry> entry = findPackEntry(packName);
        if (entry.isEmpty()) {
            return McsCommandResult.error("Unknown MCS pack '" + packName + "'.");
        }
        if (!config.isPackEnabled(entry.get().packName())) {
            return McsCommandResult.error("Pack '" + entry.get().packName() + "' is disabled.");
        }

        boolean changed = refreshPackEntry(entry.get());
        return McsCommandResult.ok(
                changed
                        ? "Reloaded pack '" + entry.get().packName() + "'."
                        : "No changes were needed for pack '" + entry.get().packName() + "'."
        );
    }

    public McsCommandResult listPacks() throws IOException {
        List<String> lines = new ArrayList<>();
        for (McsPackEntry entry : discoverPackEntries()) {
            String packState = config.isPackEnabled(entry.packName()) ? "enabled" : "disabled";
            String hotReloadState = config.isHotReloadEnabledForPack(entry.packName()) ? "on" : "off";
            lines.add(entry.packName() + " [" + sourceLabel(entry.source()) + ", pack " + packState
                    + ", hot reload " + hotReloadState + "]");
        }
        if (lines.isEmpty()) {
            return McsCommandResult.ok("No MCS packs found.");
        }
        String globalHotReload = config.hotReload() ? "enabled" : "disabled";
        return McsCommandResult.ok("Global hot reloading: " + globalHotReload + "\n" + String.join("\n", lines));
    }

    private List<Path> listPackFolders(Path root) throws IOException {
        List<Path> packs = new ArrayList<>();
        if (!Files.isDirectory(root)) {
            return packs;
        }

        try (var stream = Files.list(root)) {
            stream.filter(Files::isDirectory)
                    .filter(path -> Files.isRegularFile(path.resolve(McsPaths.PACK_FILE)))
                    .sorted()
                    .forEach(packs::add);
        }
        return packs;
    }

    private McsPackSource resolvePackSource(Path packFolder) {
        Path normalized = packFolder.toAbsolutePath().normalize();
        if (normalized.startsWith(globalMcsRoot.toAbsolutePath().normalize())) {
            return McsPackSource.GLOBAL;
        }
        return McsPackSource.WORLD;
    }

    private static String sourceLabel(McsPackSource source) {
        return source == McsPackSource.GLOBAL ? "global" : "world";
    }

    private void replaceGeneratedDatapack(Path compiledDatapack, Path target) throws IOException {
        Path backup = target.resolveSibling(target.getFileName() + ".mcs_backup");
        deleteRecursively(backup);

        boolean movedOld = false;
        if (Files.exists(target)) {
            Files.move(target, backup, StandardCopyOption.REPLACE_EXISTING);
            movedOld = true;
        }

        try {
            Files.move(compiledDatapack, target, StandardCopyOption.REPLACE_EXISTING);
            deleteRecursively(backup);
        } catch (IOException error) {
            if (movedOld && Files.exists(backup) && !Files.exists(target)) {
                Files.move(backup, target, StandardCopyOption.REPLACE_EXISTING);
            }
            throw error;
        }
    }

    private void report(String message) {
        System.out.println("[Minecraft Script] " + message);
        serverAccess.notifyOperators(message);
    }

    public static void deleteRecursively(Path path) throws IOException {
        if (path == null || !Files.exists(path)) {
            return;
        }
        Files.walkFileTree(path, new SimpleFileVisitor<>() {
            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                Files.deleteIfExists(file);
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult postVisitDirectory(Path directory, IOException exc) throws IOException {
                if (exc != null) {
                    throw exc;
                }
                Files.deleteIfExists(directory);
                return FileVisitResult.CONTINUE;
            }
        });
    }
}
