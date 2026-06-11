package dev.spyc0der.minecraftscript;

public record McsCommandResult(boolean success, String message) {
    public static McsCommandResult ok(String message) {
        return new McsCommandResult(true, message);
    }

    public static McsCommandResult error(String message) {
        return new McsCommandResult(false, message);
    }

    public McsCommandResult acknowledged(String command) {
        String prefix = command == null || command.isBlank()
                ? "MCS command acknowledged: "
                : "MCS command acknowledged: " + command + ": ";
        return new McsCommandResult(success, prefix + message);
    }
}
