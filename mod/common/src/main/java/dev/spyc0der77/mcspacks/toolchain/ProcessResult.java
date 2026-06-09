package dev.spyc0der77.mcspacks.toolchain;

public record ProcessResult(int exitCode, String stdout, String stderr) {
    public boolean success() {
        return exitCode == 0;
    }
}
