package dev.spyc0der77.mcspacks.registry;

import java.nio.file.Path;

public record PackDefinition(
        String id,
        Path folder,
        Path entryFile,
        Path compiledFolder,
        String displayName
) {
}
