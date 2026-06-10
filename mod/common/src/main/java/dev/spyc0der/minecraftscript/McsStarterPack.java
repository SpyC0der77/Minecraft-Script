package dev.spyc0der.minecraftscript;

public final class McsStarterPack {
    public static final String SOURCE = """
            function init() {
                tellraw("@a", text().text("MCS Starter Pack Loaded"));
            }

            function main() {
            }
            """;

    private McsStarterPack() {
    }
}
