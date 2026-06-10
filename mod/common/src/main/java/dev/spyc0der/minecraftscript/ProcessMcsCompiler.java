package dev.spyc0der.minecraftscript;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

public final class ProcessMcsCompiler implements McsCompiler {
    private static final long COMPILE_TIMEOUT_SECONDS = 60;

    private final McsCompilerConfig config;

    public ProcessMcsCompiler(McsCompilerConfig config) {
        this.config = config;
    }

    @Override
    public McsCompileResult compile(Path packFile, String datapackName, Path outputRoot, String minecraftVersion)
            throws IOException, InterruptedException {
        List<String> command = new ArrayList<>(McsCommandLine.split(config.pythonCommand()));
        command.add("compile");
        command.add(packFile.toString());
        command.add(datapackName);
        command.add(outputRoot.toString());
        command.add("--minecraft-version");
        command.add(minecraftVersion);

        Path logFile = Files.createTempFile(outputRoot, "mcs-compile-", ".log");
        try {
            Process process = new ProcessBuilder(command)
                    .redirectErrorStream(true)
                    .redirectOutput(logFile.toFile())
                    .start();

            boolean exited = process.waitFor(COMPILE_TIMEOUT_SECONDS, TimeUnit.SECONDS);
            String output = Files.readString(logFile, StandardCharsets.UTF_8);
            if (!exited) {
                process.destroyForcibly();
                return new McsCompileResult(124, "Minecraft-Script compile timed out after "
                        + COMPILE_TIMEOUT_SECONDS + " seconds.\n" + output);
            }
            return new McsCompileResult(process.exitValue(), output);
        } finally {
            Files.deleteIfExists(logFile);
        }
    }
}
