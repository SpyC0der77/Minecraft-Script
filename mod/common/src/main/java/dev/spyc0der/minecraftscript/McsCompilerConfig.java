package dev.spyc0der.minecraftscript;

import java.io.IOException;
import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Properties;

public record McsCompilerConfig(String pythonCommand) {
    public static final String SYSTEM_PROPERTY = "minecraft_script.pythonCommand";
    public static final String ENVIRONMENT_VARIABLE = "MCS_PYTHON_COMMAND";
    public static final String CONFIG_FILE = "mcs-mod.properties";
    public static final String CONFIG_KEY = "pythonCommand";
    public static final String DEFAULT_COMMAND = "python -m minecraft_script";

    public static McsCompilerConfig load(Path mcsRoot) {
        String configured = System.getProperty(SYSTEM_PROPERTY);
        if (configured == null || configured.isBlank()) {
            configured = System.getenv(ENVIRONMENT_VARIABLE);
        }
        if ((configured == null || configured.isBlank()) && mcsRoot != null) {
            configured = readConfigFile(mcsRoot.resolve(CONFIG_FILE));
        }
        if (configured == null || configured.isBlank()) {
            configured = DEFAULT_COMMAND;
        }
        return new McsCompilerConfig(configured.trim());
    }

    private static String readConfigFile(Path configFile) {
        if (!Files.isRegularFile(configFile)) {
            return null;
        }

        Properties properties = new Properties();
        try (Reader reader = Files.newBufferedReader(configFile)) {
            properties.load(reader);
        } catch (IOException ignored) {
            return null;
        }
        return properties.getProperty(CONFIG_KEY);
    }
}
