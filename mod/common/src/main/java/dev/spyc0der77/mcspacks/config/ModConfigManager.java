package dev.spyc0der77.mcspacks.config;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import dev.spyc0der77.mcspacks.util.McsPaths;
import java.io.IOException;
import java.nio.file.Files;

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
        } catch (IOException error) {
            throw new IllegalStateException("Failed to read mod config", error);
        }
    }

    public static void save(ModConfig config) throws IOException {
        Files.createDirectories(McsPaths.configFile().getParent());
        Files.writeString(McsPaths.configFile(), GSON.toJson(config));
    }
}
