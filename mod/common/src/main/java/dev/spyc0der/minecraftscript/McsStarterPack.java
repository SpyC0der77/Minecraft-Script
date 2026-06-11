package dev.spyc0der.minecraftscript;

public final class McsStarterPack {
    public static final String STARTER_NAME = "starter";

    public static final String STARTER_SOURCE = """
            function init() {
                tellraw("@a", text().text("MCS Starter Pack Loaded"));
            }

            function main() {
            }
            """;

    private McsStarterPack() {
    }

    public static String packSource(String packName) {
        return """
                function init() {
                    tellraw("@a", text().text("Hello from %s"));
                }

                function main() {
                }
                """.formatted(escapeForTextLiteral(packName));
    }

    public static String escapeForTextLiteral(String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    public static boolean isValidPackName(String packName) {
        if (packName == null || packName.isBlank()) {
            return false;
        }
        if (packName.equals(".") || packName.equals("..")) {
            return false;
        }
        for (int index = 0; index < packName.length(); index++) {
            char character = packName.charAt(index);
            if (character == '/' || character == '\\' || character == ':' || character == '*'
                    || character == '?' || character == '"' || character == '<' || character == '>'
                    || character == '|') {
                return false;
            }
        }
        return true;
    }
}
