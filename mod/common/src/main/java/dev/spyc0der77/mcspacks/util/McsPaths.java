package dev.spyc0der77.mcspacks.util;

import dev.architectury.platform.Platform;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

public final class McsPaths {
    public static final String PACKS_DIR = "mcs_packs";
    public static final String COMPILED_DIR = "_compiled";
    public static final String DEFAULT_ENTRY = "pack.mcs";
    public static final String CONFIG_FILE = "mcs-packs.json";

    private McsPaths() {
    }

    public static Path gameRoot() {
        return Platform.getGameFolder();
    }

    public static Path configFile() {
        return Platform.getConfigFolder().resolve(CONFIG_FILE);
    }

    public static Path packsRoot() {
        return gameRoot().resolve(PACKS_DIR);
    }

    public static Path compiledRoot() {
        return packsRoot().resolve(COMPILED_DIR);
    }

    public static Path compilerWrapper() throws IOException {
        boolean windows = isWindows();
        String resourceName = windows ? "/scripts/mcs-compile.cmd" : "/scripts/mcs-compile.sh";
        String fileName = windows ? "mcs-compile.cmd" : "mcs-compile.sh";
        Path scriptsDir = gameRoot().resolve("mcs-packs-scripts");
        Files.createDirectories(scriptsDir);
        Path wrapper = scriptsDir.resolve(fileName);
        try (InputStream stream = McsPaths.class.getResourceAsStream(resourceName)) {
            if (stream == null) {
                throw new IOException("Bundled MCS compiler wrapper is missing from the mod JAR: " + resourceName);
            }
            Files.copy(stream, wrapper, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        }
        if (!windows && !wrapper.toFile().setExecutable(true, false)) {
            throw new IOException("Failed to mark MCS compiler wrapper as executable: " + wrapper);
        }
        return wrapper;
    }

    public static Path spyglassScript() throws IOException {
        Path scriptsDir = gameRoot().resolve("mcs-packs-scripts");
        Files.createDirectories(scriptsDir);
        Path script = scriptsDir.resolve("mcs-spyglass-validate.js");
        InputStream stream = McsPaths.class.getResourceAsStream("/scripts/mcs-spyglass-validate.mjs");
        if (stream == null) {
            stream = McsPaths.class.getResourceAsStream("/scripts/mcs-spyglass-validate.js");
        }
        if (stream == null) {
            throw new IOException("Bundled Spyglass validator script is missing from the mod JAR");
        }
        try (stream) {
            Files.copy(stream, script, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        }
        return script;
    }

    public static void ensureLayout() {
        try {
            Files.createDirectories(packsRoot());
            Files.createDirectories(compiledRoot());
            Path starter = packsRoot().resolve("starter");
            Files.createDirectories(starter);
            Path starterPack = starter.resolve(DEFAULT_ENTRY);
            if (Files.notExists(starterPack)) {
                try (InputStream stream = McsPaths.class.getResourceAsStream("/starter/pack.mcs")) {
                    if (stream != null) {
                        Files.copy(stream, starterPack);
                    }
                }
            }
            Path readme = packsRoot().resolve("README.txt");
            if (Files.notExists(readme)) {
                Files.writeString(readme, """
                        MCS Packs
                        =========
                        Create one folder per datapack project under mcs_packs/.
                        Each folder needs a pack.mcs entry file.
                        Compiled output is written to mcs_packs/_compiled/.
                        Mod settings live in config/mcs-packs.json.
                        """);
            }
        } catch (IOException error) {
            throw new IllegalStateException("Failed to initialize mcs_packs folders", error);
        }
    }

    private static boolean isWindows() {
        String os = System.getProperty("os.name", "");
        return os.toLowerCase(Locale.ROOT).contains("win");
    }
}
