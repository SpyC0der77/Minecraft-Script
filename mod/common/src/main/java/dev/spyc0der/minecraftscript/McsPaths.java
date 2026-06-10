package dev.spyc0der.minecraftscript;

import java.nio.file.Path;
import java.util.Locale;
import java.util.Optional;

public final class McsPaths {
    public static final String SOURCE_ROOT = "mcs_packs";
    public static final String DATAPACK_ROOT = "datapacks";
    public static final String PACK_FILE = "pack.mcs";
    public static final String GENERATED_PREFIX = "mcs_";

    private McsPaths() {
    }

    public static Path mcsPacksRoot(Path saveRoot) {
        return saveRoot.resolve(SOURCE_ROOT);
    }

    public static Path datapacksRoot(Path saveRoot) {
        return saveRoot.resolve(DATAPACK_ROOT);
    }

    public static Optional<Path> packFolderForChangedPath(Path mcsRoot, Path changedPath) {
        Path normalizedRoot = mcsRoot.toAbsolutePath().normalize();
        Path normalizedChanged = changedPath.toAbsolutePath().normalize();
        if (!normalizedChanged.startsWith(normalizedRoot)) {
            return Optional.empty();
        }

        Path relative = normalizedRoot.relativize(normalizedChanged);
        if (relative.getNameCount() == 0) {
            return Optional.empty();
        }
        return Optional.of(normalizedRoot.resolve(relative.getName(0)));
    }

    public static String sanitizePackFolderName(String folderName) {
        String sanitized = folderName.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9._-]+", "_");
        sanitized = sanitized.replaceAll("_+", "_").replaceAll("^_+|_+$", "");
        return sanitized.isBlank() ? "pack" : sanitized;
    }

    public static String generatedDatapackName(Path packFolder) {
        return GENERATED_PREFIX + sanitizePackFolderName(packFolder.getFileName().toString());
    }
}
