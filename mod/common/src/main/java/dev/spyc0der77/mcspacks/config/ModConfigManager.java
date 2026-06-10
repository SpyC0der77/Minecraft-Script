package dev.spyc0der77.mcspacks.config;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonParseException;
import dev.spyc0der77.mcspacks.util.McsPaths;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;

public final class ModConfigManager {
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    private ModConfigManager() {
    }

    public static ModConfig load() {
        try {
            if (Files.notExists(McsPaths.configFile())) {
                ModConfig defaults = new ModConfig();
                save(defaults);
                return defaults;
            }
            String json = Files.readString(McsPaths.configFile());
            ModConfig config = GSON.fromJson(json, ModConfig.class);
            return config == null ? new ModConfig() : config;
        } catch (JsonParseException error) {
            System.err.println("[MCS Packs] Invalid config JSON, using defaults: " + error.getMessage());
            return new ModConfig();
        } catch (IOException error) {
            System.err.println("[MCS Packs] Failed to read config, using defaults: " + error.getMessage());
            return new ModConfig();
        }
    }

    public static void save(ModConfig config) throws IOException {
        Path configFile = McsPaths.configFile();
        Files.createDirectories(configFile.getParent());
        Path tempFile = Files.createTempFile(configFile.getParent(), "mcs-packs-", ".json.tmp");
        try {
            Files.writeString(tempFile, GSON.toJson(config));
            Files.move(tempFile, configFile, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
        } finally {
            Files.deleteIfExists(tempFile);
        }
    }
}
