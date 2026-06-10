package dev.spyc0der.minecraftscript;

import java.io.IOException;
import java.nio.file.Path;

public interface McsCompiler {
    McsCompileResult compile(Path packFile, String datapackName, Path outputRoot, String minecraftVersion)
            throws IOException, InterruptedException;
}
