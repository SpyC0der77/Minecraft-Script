package dev.spyc0der77.mcspacks.toolchain;

import dev.spyc0der77.mcspacks.config.ModConfig;
import dev.spyc0der77.mcspacks.util.McsPaths;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public final class CompilerResolver {
    private static final Object CACHE_LOCK = new Object();
    private static volatile String cachedKey;
    private static volatile CompilerCommand cachedCommand;

    private CompilerResolver() {
    }

    public record CompilerCommand(String executable, List<String> baseArgs, boolean windowsBatch) {
        List<String> toProcessCommand(List<String> args) {
            List<String> allArgs = new ArrayList<>(baseArgs);
            allArgs.addAll(args);
            if (windowsBatch && isWindows()) {
                return List.of("cmd.exe", "/c", buildCmdInvocation(executable, allArgs));
            }
            List<String> command = new ArrayList<>();
            command.add(executable);
            command.addAll(allArgs);
            return command;
        }
    }

    public static CompilerCommand resolve(ModConfig config) {
        String key = (config.compiler == null ? "auto" : config.compiler) + "|" + config.compilerPath;
        synchronized (CACHE_LOCK) {
            if (key.equals(cachedKey) && cachedCommand != null) {
                return cachedCommand;
            }
            CompilerCommand resolved = resolveUncached(config);
            cachedKey = key;
            cachedCommand = resolved;
            return resolved;
        }
    }

    private static CompilerCommand resolveUncached(ModConfig config) {
        String mode = config.compiler == null ? "auto" : config.compiler.toLowerCase(Locale.ROOT);
        if (config.compilerPath != null && !config.compilerPath.isBlank()) {
            return fromExplicitPath(config.compilerPath, mode);
        }
        return switch (mode) {
            case "python" -> resolvePython();
            case "mcs" -> new CompilerCommand("mcs", List.of(), false);
            default -> resolveAuto();
        };
    }

    private static CompilerCommand fromExplicitPath(String compilerPath, String mode) {
        if ("python".equals(mode) || looksLikePython(compilerPath)) {
            return new CompilerCommand(compilerPath, List.of("-m", "minecraft_script"), isBatch(compilerPath));
        }
        return new CompilerCommand(compilerPath, List.of(), isBatch(compilerPath));
    }

    private static CompilerCommand resolveAuto() {
        CompilerCommand mcs = new CompilerCommand("mcs", List.of(), false);
        if (canRun(mcs, "lint", "--help")) {
            return mcs;
        }
        CompilerCommand python = resolvePython();
        if (canRun(python, "lint", "--help")) {
            return python;
        }
        try {
            Path wrapper = McsPaths.compilerWrapper();
            return new CompilerCommand(wrapper.toString(), List.of(), true);
        } catch (IOException error) {
            return new CompilerCommand("mcs", List.of(), false);
        }
    }

    private static CompilerCommand resolvePython() {
        if (System.getenv("PYTHON") != null && Files.isExecutable(Path.of(System.getenv("PYTHON")))) {
            CompilerCommand resolved = pythonCommand(System.getenv("PYTHON"));
            if (canRun(resolved, "lint", "--help")) {
                return resolved;
            }
        }
        for (String version : List.of("313", "312", "311", "310")) {
            for (Path candidate : knownPythonInstalls(version)) {
                if (!Files.isExecutable(candidate)) {
                    continue;
                }
                CompilerCommand resolved = pythonCommand(candidate.toString());
                if (canRun(resolved, "lint", "--help")) {
                    return resolved;
                }
            }
        }
        for (String candidate : List.of("python", "python3", "py")) {
            CompilerCommand resolved = "py".equals(candidate)
                    ? new CompilerCommand(candidate, List.of("-3", "-m", "minecraft_script"), false)
                    : pythonCommand(candidate);
            if (canRun(resolved, "lint", "--help")) {
                return resolved;
            }
        }
        return pythonCommand("python");
    }

    private static List<Path> knownPythonInstalls(String version) {
        List<Path> candidates = new ArrayList<>();
        if (isWindows()) {
            String localAppData = System.getenv("LOCALAPPDATA");
            String programFiles = System.getenv("PROGRAMFILES");
            candidates.add(Path.of("C:\\Python" + version + "\\python.exe"));
            if (localAppData != null) {
                candidates.add(Path.of(localAppData, "Programs", "Python", "Python" + version, "python.exe"));
                candidates.add(Path.of(localAppData, "Microsoft", "WindowsApps", "python.exe"));
            }
            if (programFiles != null) {
                candidates.add(Path.of(programFiles, "Python" + version, "python.exe"));
            }
        } else {
            candidates.add(Path.of("/usr/local/bin/python" + version));
            candidates.add(Path.of("/usr/bin/python" + version));
        }
        return candidates;
    }

    private static CompilerCommand pythonCommand(String executable) {
        return new CompilerCommand(executable, List.of("-m", "minecraft_script"), isBatch(executable));
    }

    private static boolean looksLikePython(String compilerPath) {
        String lower = compilerPath.toLowerCase(Locale.ROOT);
        return lower.endsWith("python.exe") || lower.endsWith("python") || lower.endsWith("python3");
    }

    private static boolean isBatch(String compilerPath) {
        String lower = compilerPath.toLowerCase(Locale.ROOT);
        return lower.endsWith(".cmd") || lower.endsWith(".bat");
    }

    private static boolean canRun(CompilerCommand compiler, String... args) {
        try {
            ProcessResult result = SubprocessRunner.run(compiler.toProcessCommand(List.of(args)), null, 15);
            return result.success();
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            return false;
        } catch (Exception ignored) {
            return false;
        }
    }

    private static boolean isWindows() {
        String os = System.getProperty("os.name", "");
        return os.toLowerCase(Locale.ROOT).contains("win");
    }

    private static String buildCmdInvocation(String executable, List<String> args) {
        StringBuilder command = new StringBuilder();
        command.append('"').append(executable).append('"');
        for (String arg : args) {
            command.append(' ').append(quoteForCmd(arg));
        }
        return command.toString();
    }

    private static String quoteForCmd(String arg) {
        if (!needsCmdQuoting(arg)) {
            return arg;
        }
        return "\"" + arg.replace("\"", "\\\"").replace("%", "%%") + "\"";
    }

    private static boolean needsCmdQuoting(String arg) {
        if (arg.isEmpty()) {
            return true;
        }
        for (int index = 0; index < arg.length(); index++) {
            char character = arg.charAt(index);
            if (Character.isWhitespace(character)
                    || character == '"'
                    || character == '&'
                    || character == '|'
                    || character == '<'
                    || character == '>'
                    || character == '^'
                    || character == '%') {
                return true;
            }
        }
        return false;
    }
}
