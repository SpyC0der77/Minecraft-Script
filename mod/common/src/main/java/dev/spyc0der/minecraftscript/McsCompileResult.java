package dev.spyc0der.minecraftscript;

public record McsCompileResult(int exitCode, String output) {
    public boolean succeeded() {
        return exitCode == 0;
    }
}
