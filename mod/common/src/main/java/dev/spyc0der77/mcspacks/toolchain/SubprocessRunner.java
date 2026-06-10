package dev.spyc0der77.mcspacks.toolchain;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

public final class SubprocessRunner {
    private SubprocessRunner() {
    }

    public static ProcessResult run(List<String> command, Path workingDirectory, long timeoutSeconds) throws IOException, InterruptedException {
        ProcessBuilder builder = new ProcessBuilder(command);
        if (workingDirectory != null) {
            builder.directory(workingDirectory.toFile());
        }
        builder.redirectErrorStream(false);
        Process process = builder.start();
        CompletableFuture<String> stdoutFuture = CompletableFuture.supplyAsync(() -> readStream(process.getInputStream()));
        CompletableFuture<String> stderrFuture = CompletableFuture.supplyAsync(() -> readStream(process.getErrorStream()));
        try {
            boolean finished = process.waitFor(timeoutSeconds, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                process.waitFor();
                return new ProcessResult(-1, "", "Process timed out after " + timeoutSeconds + "s");
            }
            return new ProcessResult(process.exitValue(), stdoutFuture.join(), stderrFuture.join());
        } catch (InterruptedException error) {
            process.destroyForcibly();
            process.waitFor();
            Thread.currentThread().interrupt();
            return new ProcessResult(-1, "", "Process interrupted");
        }
    }

    private static String readStream(java.io.InputStream stream) {
        try {
            return new String(stream.readAllBytes(), StandardCharsets.UTF_8);
        } catch (IOException ignored) {
            return "";
        }
    }
}
