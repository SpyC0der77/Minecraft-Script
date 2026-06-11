package dev.spyc0der.minecraftscript;

import java.nio.file.Path;
import java.util.Objects;

public record McsPackEntry(Path packFolder, McsPackSource source) {
    public McsPackEntry {
        Objects.requireNonNull(packFolder, "packFolder");
        Objects.requireNonNull(source, "source");
    }

    public String packName() {
        return packFolder.getFileName().toString();
    }
}
