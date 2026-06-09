package dev.spyc0der77.mcspacks.toolchain;

public record Diagnostic(String file, int line, int column, String message, String severity) {
    public boolean isError() {
        return "error".equalsIgnoreCase(severity);
    }
}
