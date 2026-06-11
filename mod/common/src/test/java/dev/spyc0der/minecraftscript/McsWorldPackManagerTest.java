package dev.spyc0der.minecraftscript;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class McsWorldPackManagerTest {
    @TempDir
    Path tempDir;

    @Test
    void createsStarterPackInGlobalFolder() throws IOException {
        McsWorldPackManager manager = newManager(new SuccessfulCompiler());

        manager.initializeWorldFolders();
        Files.createDirectories(tempDir.resolve("mcs_packs/custom"));
        Files.writeString(tempDir.resolve("mcs_packs/custom/pack.mcs"), "function main() {}");

        List<String> packNames = manager.discoverPackEntries().stream()
                .map(McsPackEntry::packName)
                .sorted()
                .toList();

        assertEquals(List.of("custom", "starter"), packNames);
        assertTrue(Files.readString(tempDir.resolve("global/mcs_packs/starter/pack.mcs"))
                .contains("MCS Starter Pack Loaded"));
        assertEquals(
                McsPackSource.GLOBAL,
                manager.findPackEntry("starter").orElseThrow().source()
        );
    }

    @Test
    void discoversGlobalAndWorldPacksWithWorldTakingPrecedence() throws IOException {
        McsWorldPackManager manager = newManager(new SuccessfulCompiler());
        manager.initializeWorldFolders();

        Files.createDirectories(tempDir.resolve("global/mcs_packs/shared"));
        Files.writeString(tempDir.resolve("global/mcs_packs/shared/pack.mcs"), "function main() {}");
        Files.createDirectories(tempDir.resolve("mcs_packs/shared"));
        Files.writeString(tempDir.resolve("mcs_packs/shared/pack.mcs"), "function main() {}");
        Files.createDirectories(tempDir.resolve("mcs_packs/global-only"));
        Files.writeString(tempDir.resolve("mcs_packs/global-only/pack.mcs"), "function main() {}");

        List<String> packNames = manager.discoverPackEntries().stream()
                .map(McsPackEntry::packName)
                .sorted()
                .toList();

        assertEquals(List.of("global-only", "shared", "starter"), packNames);
        assertEquals(
                McsPackSource.WORLD,
                manager.findPackEntry("shared").orElseThrow().source()
        );
        assertEquals(
                McsPackSource.GLOBAL,
                manager.findPackEntry("starter").orElseThrow().source()
        );
    }

    @Test
    void createPackWritesHelloMessageAndCompiles() throws IOException {
        McsWorldPackManager manager = newManager(new SuccessfulCompiler());
        manager.initializeWorldFolders();

        McsCommandResult result = manager.createPack("Demo", McsPackSource.WORLD);
        assertTrue(result.success());
        assertTrue(Files.readString(tempDir.resolve("mcs_packs/Demo/pack.mcs")).contains("Hello from Demo"));
        assertTrue(Files.isDirectory(tempDir.resolve("datapacks/mcs_demo")));

        McsCommandResult duplicate = manager.createPack("Demo", McsPackSource.GLOBAL);
        assertFalse(duplicate.success());
    }

    @Test
    void createGlobalPackUsesGlobalFolder() throws IOException {
        McsWorldPackManager manager = newManager(new SuccessfulCompiler());
        manager.initializeWorldFolders();

        McsCommandResult result = manager.createPack("Shared", McsPackSource.GLOBAL);
        assertTrue(result.success());
        assertTrue(Files.isRegularFile(tempDir.resolve("global/mcs_packs/Shared/pack.mcs")));
        assertTrue(Files.isDirectory(tempDir.resolve("datapacks/mcs_global_shared")));
    }

    @Test
    void sanitizesGeneratedDatapackNames() {
        assertEquals("mcs_my_pack_1", McsPaths.generatedDatapackName(Path.of("My Pack 1")));
        assertEquals("mcs_global_my_pack_1", McsPaths.generatedDatapackName(Path.of("My Pack 1"), McsPackSource.GLOBAL));
        assertEquals("pack", McsPaths.sanitizePackFolderName("!!!"));
    }

    @Test
    void successfulCompileReplacesGeneratedDatapack() throws IOException {
        McsWorldPackManager manager = newManager(new SuccessfulCompiler());
        manager.initializeWorldFolders();
        Path packFolder = tempDir.resolve("mcs_packs/My Pack");
        Files.createDirectories(packFolder);
        Files.writeString(packFolder.resolve("pack.mcs"), "function main() {}");

        assertTrue(manager.compilePack(packFolder));

        Path generated = tempDir.resolve("datapacks/mcs_my_pack");
        assertTrue(Files.isDirectory(generated));
        assertEquals("compiled", Files.readString(generated.resolve("pack.mcmeta")));
    }

    @Test
    void globalPacksCompileToGlobalDatapackPrefix() throws IOException {
        McsWorldPackManager manager = newManager(new SuccessfulCompiler());
        manager.initializeWorldFolders();
        Path packFolder = tempDir.resolve("global/mcs_packs/My Pack");
        Files.createDirectories(packFolder);
        Files.writeString(packFolder.resolve("pack.mcs"), "function main() {}");

        McsPackEntry entry = manager.findPackEntry("My Pack").orElseThrow();
        assertEquals(McsPackSource.GLOBAL, entry.source());
        assertTrue(manager.compilePack(entry));

        assertTrue(Files.isDirectory(tempDir.resolve("datapacks/mcs_global_my_pack")));
    }

    @Test
    void failedCompileKeepsExistingDatapack() throws IOException {
        Path generated = tempDir.resolve("datapacks/mcs_global_starter");
        Files.createDirectories(generated);
        Files.writeString(generated.resolve("pack.mcmeta"), "old");

        McsWorldPackManager manager = newManager(new FailingCompiler());
        manager.initializeWorldFolders();

        assertFalse(manager.compilePack(manager.findPackEntry("starter").orElseThrow()));
        assertEquals("old", Files.readString(generated.resolve("pack.mcmeta")));
    }

    @Test
    void disabledPacksAreSkippedAndRemoved() throws IOException {
        McsModConfig config = new McsModConfig(McsModConfig.DEFAULT_COMMAND, true, Set.of(), Set.of("starter"));
        McsWorldPackManager manager = new McsWorldPackManager(new TestServerAccess(tempDir), new SuccessfulCompiler(), config);
        manager.initializeWorldFolders();

        Path generated = tempDir.resolve("datapacks/mcs_global_starter");
        Files.createDirectories(generated);
        Files.writeString(generated.resolve("pack.mcmeta"), "old");

        McsPackEntry starter = manager.findPackEntry("starter").orElseThrow();
        assertTrue(manager.refreshPackEntry(starter));
        assertFalse(Files.exists(generated));
    }

    @Test
    void deletedPackRemovesGeneratedDatapack() throws IOException {
        McsWorldPackManager manager = newManager(new SuccessfulCompiler());
        manager.initializeWorldFolders();
        Path generated = tempDir.resolve("datapacks/mcs_global_starter");
        Files.createDirectories(generated);
        Files.writeString(generated.resolve("pack.mcmeta"), "old");
        Files.delete(tempDir.resolve("global/mcs_packs/starter/pack.mcs"));

        assertTrue(manager.refreshPack(tempDir.resolve("global/mcs_packs/starter")));
        assertFalse(Files.exists(generated));
    }

    @Test
    void savesConfigToProfileDirectory() throws IOException {
        McsWorldPackManager manager = newManager(new SuccessfulCompiler());
        manager.initializeWorldFolders();

        McsCommandResult result = manager.setHotReloading(false, null);
        assertTrue(result.success());
        assertTrue(Files.isRegularFile(tempDir.resolve("global/mcs-mod.properties")));
        assertFalse(Files.exists(tempDir.resolve("mcs_packs/mcs-mod.properties")));
    }

    private McsWorldPackManager newManager(McsCompiler compiler) {
        return new McsWorldPackManager(
                new TestServerAccess(tempDir),
                compiler,
                McsModConfig.load(tempDir.resolve("global"))
        );
    }

    private record TestServerAccess(Path saveRoot) implements McsServerAccess {
        @Override
        public Path serverDirectory() {
            return saveRoot.resolve("global");
        }

        @Override
        public String minecraftVersion() {
            return "1.21.2";
        }

        @Override
        public void executeReload() {
        }

        @Override
        public void executeStartupReload() {
        }

        @Override
        public void notifyOperators(String message) {
        }
    }

    private static final class SuccessfulCompiler implements McsCompiler {
        final List<Path> compiled = new ArrayList<>();

        @Override
        public McsCompileResult compile(Path packFile, String datapackName, Path outputRoot, String minecraftVersion)
                throws IOException {
            compiled.add(packFile);
            Path generated = outputRoot.resolve(datapackName);
            Files.createDirectories(generated);
            Files.writeString(generated.resolve("pack.mcmeta"), "compiled");
            return new McsCompileResult(0, "ok");
        }
    }

    private static final class FailingCompiler implements McsCompiler {
        @Override
        public McsCompileResult compile(Path packFile, String datapackName, Path outputRoot, String minecraftVersion) {
            return new McsCompileResult(1, "syntax error");
        }
    }
}
