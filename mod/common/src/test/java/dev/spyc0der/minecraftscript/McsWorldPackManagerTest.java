package dev.spyc0der.minecraftscript;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class McsWorldPackManagerTest {
    @TempDir
    Path tempDir;

    @Test
    void createsStarterPackAndDiscoversOnlyPackFolders() throws IOException {
        McsWorldPackManager manager = newManager(new SuccessfulCompiler());

        manager.initializeWorldFolders();
        Files.createDirectories(tempDir.resolve("mcs_packs/empty"));
        Files.createDirectories(tempDir.resolve("mcs_packs/custom"));
        Files.writeString(tempDir.resolve("mcs_packs/custom/pack.mcs"), "function main() {}");

        List<String> packNames = manager.discoverPackFolders().stream()
                .map(path -> path.getFileName().toString())
                .toList();

        assertEquals(List.of("custom", "starter"), packNames);
        assertTrue(Files.readString(tempDir.resolve("mcs_packs/starter/pack.mcs"))
                .contains("MCS Starter Pack Loaded"));
    }

    @Test
    void sanitizesGeneratedDatapackNames() {
        assertEquals("mcs_my_pack_1", McsPaths.generatedDatapackName(Path.of("My Pack 1")));
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
    void failedCompileKeepsExistingDatapack() throws IOException {
        Path generated = tempDir.resolve("datapacks/mcs_starter");
        Files.createDirectories(generated);
        Files.writeString(generated.resolve("pack.mcmeta"), "old");

        McsWorldPackManager manager = newManager(new FailingCompiler());
        manager.initializeWorldFolders();

        assertFalse(manager.compilePack(tempDir.resolve("mcs_packs/starter")));
        assertEquals("old", Files.readString(generated.resolve("pack.mcmeta")));
    }

    @Test
    void deletedPackRemovesGeneratedDatapack() throws IOException {
        McsWorldPackManager manager = newManager(new SuccessfulCompiler());
        manager.initializeWorldFolders();
        Path generated = tempDir.resolve("datapacks/mcs_starter");
        Files.createDirectories(generated);
        Files.writeString(generated.resolve("pack.mcmeta"), "old");
        Files.delete(tempDir.resolve("mcs_packs/starter/pack.mcs"));

        assertTrue(manager.refreshPack(tempDir.resolve("mcs_packs/starter")));
        assertFalse(Files.exists(generated));
    }

    private McsWorldPackManager newManager(McsCompiler compiler) {
        return new McsWorldPackManager(new TestServerAccess(tempDir), compiler);
    }

    private record TestServerAccess(Path saveRoot) implements McsServerAccess {
        @Override
        public String minecraftVersion() {
            return "1.21.2";
        }

        @Override
        public void executeReload() {
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
