package dev.spyc0der.minecraftscript;

import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Properties;
import java.util.Set;
import java.util.stream.Collectors;

public record McsModConfig(
        String pythonCommand,
        boolean hotReload,
        Set<String> hotReloadDisabledPacks,
        Set<String> disabledPacks
) {
    public static final String SYSTEM_PROPERTY_PYTHON = "minecraft_script.pythonCommand";
    public static final String ENVIRONMENT_VARIABLE_PYTHON = "MCS_PYTHON_COMMAND";
    public static final String CONFIG_FILE = "mcs-mod.properties";
    public static final String KEY_PYTHON_COMMAND = "pythonCommand";
    public static final String KEY_HOT_RELOAD = "hotReload";
    public static final String KEY_HOT_RELOAD_DISABLED_PACKS = "hotReloadDisabledPacks";
    public static final String KEY_DISABLED_PACKS = "disabledPacks";
    public static final String DEFAULT_COMMAND = "python -m minecraft_script";

    public McsModConfig {
        pythonCommand = pythonCommand == null || pythonCommand.isBlank() ? DEFAULT_COMMAND : pythonCommand.trim();
        hotReloadDisabledPacks = normalizePackSet(hotReloadDisabledPacks);
        disabledPacks = normalizePackSet(disabledPacks);
    }

    public static McsModConfig load(Path configDirectory) {
        Properties properties = new Properties();
        Path configFile = configDirectory.resolve(CONFIG_FILE);
        if (Files.isRegularFile(configFile)) {
            try (Reader reader = Files.newBufferedReader(configFile)) {
                properties.load(reader);
            } catch (IOException ignored) {
            }
        }

        String pythonCommand = System.getProperty(SYSTEM_PROPERTY_PYTHON);
        if (pythonCommand == null || pythonCommand.isBlank()) {
            pythonCommand = System.getenv(ENVIRONMENT_VARIABLE_PYTHON);
        }
        if (pythonCommand == null || pythonCommand.isBlank()) {
            pythonCommand = properties.getProperty(KEY_PYTHON_COMMAND);
        }

        boolean hotReload = parseBoolean(properties.getProperty(KEY_HOT_RELOAD), true);
        Set<String> hotReloadDisabledPacks = parsePackSet(properties.getProperty(KEY_HOT_RELOAD_DISABLED_PACKS));
        Set<String> disabledPacks = parsePackSet(properties.getProperty(KEY_DISABLED_PACKS));

        return new McsModConfig(pythonCommand, hotReload, hotReloadDisabledPacks, disabledPacks);
    }

    public void save(Path configDirectory) throws IOException {
        Files.createDirectories(configDirectory);
        Properties properties = new Properties();
        properties.setProperty(KEY_PYTHON_COMMAND, pythonCommand);
        properties.setProperty(KEY_HOT_RELOAD, Boolean.toString(hotReload));
        writePackSetProperty(properties, KEY_HOT_RELOAD_DISABLED_PACKS, hotReloadDisabledPacks);
        writePackSetProperty(properties, KEY_DISABLED_PACKS, disabledPacks);

        Path configFile = configDirectory.resolve(CONFIG_FILE);
        try (Writer writer = Files.newBufferedWriter(configFile)) {
            properties.store(writer, "Minecraft Script mod settings");
        }
    }

    public boolean isPackEnabled(String packName) {
        return !disabledPacks.contains(normalizePackName(packName));
    }

    public boolean isHotReloadEnabledForPack(String packName) {
        return hotReload && !hotReloadDisabledPacks.contains(normalizePackName(packName));
    }

    public McsModConfig withHotReload(boolean value) {
        return new McsModConfig(pythonCommand, value, hotReloadDisabledPacks, disabledPacks);
    }

    public McsModConfig withHotReloadForPack(String packName, boolean enabled) {
        String normalized = normalizePackName(packName);
        LinkedHashSet<String> updated = new LinkedHashSet<>(hotReloadDisabledPacks);
        if (enabled) {
            updated.remove(normalized);
        } else {
            updated.add(normalized);
        }
        return new McsModConfig(pythonCommand, hotReload, updated, disabledPacks);
    }

    public McsModConfig withPackEnabled(String packName, boolean enabled) {
        String normalized = normalizePackName(packName);
        LinkedHashSet<String> updated = new LinkedHashSet<>(disabledPacks);
        if (enabled) {
            updated.remove(normalized);
        } else {
            updated.add(normalized);
        }
        return new McsModConfig(pythonCommand, hotReload, hotReloadDisabledPacks, updated);
    }

    public static String normalizePackName(String packName) {
        return packName.trim().toLowerCase(Locale.ROOT);
    }

    private static Set<String> normalizePackSet(Set<String> packNames) {
        if (packNames == null || packNames.isEmpty()) {
            return Set.of();
        }
        return packNames.stream()
                .map(McsModConfig::normalizePackName)
                .filter(name -> !name.isBlank())
                .collect(Collectors.toCollection(LinkedHashSet::new));
    }

    private static boolean parseBoolean(String value, boolean defaultValue) {
        if (value == null || value.isBlank()) {
            return defaultValue;
        }
        return Boolean.parseBoolean(value.trim());
    }

    private static Set<String> parsePackSet(String value) {
        if (value == null || value.isBlank()) {
            return Set.of();
        }
        return Arrays.stream(value.split(","))
                .map(McsModConfig::normalizePackName)
                .filter(name -> !name.isBlank())
                .collect(Collectors.toCollection(LinkedHashSet::new));
    }

    private static void writePackSetProperty(Properties properties, String key, Set<String> packNames) {
        if (packNames.isEmpty()) {
            properties.remove(key);
            return;
        }
        properties.setProperty(key, packNames.stream().sorted().collect(Collectors.joining(",")));
    }
}
