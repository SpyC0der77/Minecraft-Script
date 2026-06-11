package dev.spyc0der.minecraftscript;

import java.nio.file.Path;
import java.util.List;
import java.util.Locale;
import java.util.Optional;

public final class McsPaths {
    public static final String SOURCE_ROOT = "mcs_packs";
    public static final String DATAPACK_ROOT = "datapacks";
    public static final String PACK_FILE = "pack.mcs";
    public static final String GENERATED_PREFIX = "mcs_";

    private McsPaths() {
    }

    public static Path worldMcsPacksRoot(Path saveRoot) {
        return saveRoot.resolve(SOURCE_ROOT);
    }

    public static Path mcsPacksRoot(Path saveRoot) {
        return worldMcsPacksRoot(saveRoot);
    }

    public static Path globalMcsPacksRoot(Path serverDirectory) {
        return serverDirectory.resolve(SOURCE_ROOT);
    }

    public static Path configDirectory(Path serverDirectory) {
        return serverDirectory;
    }

    public static Path datapacksRoot(Path saveRoot) {
        return saveRoot.resolve(DATAPACK_ROOT);
    }

    public static Optional<Path> packFolderForChangedPath(List<Path> mcsRoots, Path changedPath) {
        for (Path mcsRoot : mcsRoots) {
            Optional<Path> packFolder = packFolderForChangedPath(mcsRoot, changedPath);
            if (packFolder.isPresent()) {
                return packFolder;
            }
        }
        return Optional.empty();
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
        return generatedDatapackName(packFolder, McsPackSource.WORLD);
    }

    public static String generatedDatapackName(Path packFolder, McsPackSource source) {
        String sanitized = sanitizePackFolderName(packFolder.getFileName().toString());
        if (source == McsPackSource.GLOBAL) {
            return GENERATED_PREFIX + "global_" + sanitized;
        }
        return GENERATED_PREFIX + sanitized;
    }

    public static String packKey(String packName) {
        return McsModConfig.normalizePackName(packName);
    }
}
