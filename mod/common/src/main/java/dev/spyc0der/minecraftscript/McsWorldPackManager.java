package dev.spyc0der.minecraftscript;

import java.io.IOException;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

public final class McsWorldPackManager {
    private final Path saveRoot;
    private final Path mcsRoot;
    private final Path datapacksRoot;
    private final String minecraftVersion;
    private final McsCompiler compiler;
    private final McsServerAccess serverAccess;

    public McsWorldPackManager(McsServerAccess serverAccess, McsCompiler compiler) {
        this.serverAccess = Objects.requireNonNull(serverAccess, "serverAccess");
        this.compiler = Objects.requireNonNull(compiler, "compiler");
        this.saveRoot = serverAccess.saveRoot();
        this.mcsRoot = McsPaths.mcsPacksRoot(saveRoot);
        this.datapacksRoot = McsPaths.datapacksRoot(saveRoot);
        this.minecraftVersion = serverAccess.minecraftVersion();
    }

    public Path mcsRoot() {
        return mcsRoot;
    }

    public void initializeWorldFolders() throws IOException {
        Files.createDirectories(mcsRoot);
        Files.createDirectories(datapacksRoot);

        Path starterPack = mcsRoot.resolve("starter").resolve(McsPaths.PACK_FILE);
        if (!Files.exists(starterPack)) {
            Files.createDirectories(starterPack.getParent());
            Files.writeString(starterPack, McsStarterPack.SOURCE);
        }
    }

    public List<Path> discoverPackFolders() throws IOException {
        List<Path> packs = new ArrayList<>();
        if (!Files.isDirectory(mcsRoot)) {
            return packs;
        }

        try (var stream = Files.list(mcsRoot)) {
            stream.filter(Files::isDirectory)
                    .filter(path -> Files.isRegularFile(path.resolve(McsPaths.PACK_FILE)))
                    .sorted()
                    .forEach(packs::add);
        }
        return packs;
    }

    public boolean compileAll() {
        boolean changed = false;
        try {
            for (Path packFolder : discoverPackFolders()) {
                changed |= compilePack(packFolder);
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
        Path packFile = packFolder.resolve(McsPaths.PACK_FILE);
        if (Files.isRegularFile(packFile)) {
            return compilePack(packFolder);
        }
        return deleteGeneratedPack(packFolder);
    }

    public boolean compilePack(Path packFolder) {
        String datapackName = McsPaths.generatedDatapackName(packFolder);
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
            report("Compiled MCS pack " + packFolder.getFileName() + " for Minecraft " + minecraftVersion);
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
        Path target = datapacksRoot.resolve(McsPaths.generatedDatapackName(packFolder));
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
