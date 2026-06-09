package dev.spyc0der77.mcspacks.registry;

import com.google.gson.Gson;
import com.google.gson.JsonParseException;
import dev.spyc0der77.mcspacks.util.McsPaths;
import dev.spyc0der77.mcspacks.util.SafePaths;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public final class PackRegistry {
    private final Path packsRoot;
    private final Path compiledRoot;

    public PackRegistry(Path packsRoot, Path compiledRoot) {
        this.packsRoot = packsRoot;
        this.compiledRoot = compiledRoot;
    }

    public List<PackDefinition> discover() throws IOException {
        List<PackDefinition> packs = new ArrayList<>();
        if (Files.notExists(packsRoot)) {
            return packs;
        }
        try (var stream = Files.list(packsRoot)) {
            for (Path folder : stream.toList()) {
                if (!Files.isDirectory(folder)) {
                    continue;
                }
                String name = folder.getFileName().toString();
                if (name.startsWith("_") || name.startsWith(".")) {
                    continue;
                }
                PackDefinition pack = resolvePack(folder);
                if (pack != null) {
                    packs.add(pack);
                }
            }
        }
        return packs;
    }

    public PackDefinition resolvePack(Path folder) throws IOException {
        PackOverrides overrides = readOverrides(folder);
        Path entry = folder.resolve(overrides.entryFile == null ? McsPaths.DEFAULT_ENTRY : overrides.entryFile);
        if (Files.notExists(entry)) {
            return null;
        }
        String id = folder.getFileName().toString();
        String displayName = overrides.displayName == null
                ? titleCase(id)
                : overrides.displayName;
        SafePaths.validateSafeName(displayName);
        return new PackDefinition(
                id,
                folder,
                entry,
                SafePaths.resolveChild(compiledRoot, displayName),
                displayName
        );
    }

    private PackOverrides readOverrides(Path folder) throws IOException {
        Path config = folder.resolve("pack.json");
        if (Files.notExists(config)) {
            return new PackOverrides();
        }
        try {
            PackOverrides overrides = new Gson().fromJson(Files.readString(config), PackOverrides.class);
            return overrides == null ? new PackOverrides() : overrides;
        } catch (JsonParseException error) {
            return new PackOverrides();
        }
    }

    private static String titleCase(String value) {
        String[] parts = value.replace('-', '_').split("_");
        StringBuilder builder = new StringBuilder();
        for (String part : parts) {
            if (part.isBlank()) {
                continue;
            }
            if (!builder.isEmpty()) {
                builder.append(' ');
            }
            builder.append(part.substring(0, 1).toUpperCase(Locale.ROOT));
            if (part.length() > 1) {
                builder.append(part.substring(1).toLowerCase(Locale.ROOT));
            }
        }
        return builder.isEmpty() ? value : builder.toString();
    }

    private static final class PackOverrides {
        private String displayName;
        private String entryFile;
    }
}
