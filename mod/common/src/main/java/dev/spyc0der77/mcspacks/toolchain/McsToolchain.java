package dev.spyc0der77.mcspacks.toolchain;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import dev.spyc0der77.mcspacks.config.ModConfig;
import dev.spyc0der77.mcspacks.registry.PackDefinition;
import dev.spyc0der77.mcspacks.util.McsPaths;
import java.io.IOException;
import java.lang.reflect.Type;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class McsToolchain {
    private static final Gson GSON = new Gson();
    private static final Type DIAGNOSTIC_LIST = new TypeToken<List<Diagnostic>>() {}.getType();

    private final ModConfig config;
    private final String mcsProfile;
    private final CompilerResolver.CompilerCommand compiler;

    public McsToolchain(ModConfig config, String mcsProfile) {
        this.config = config;
        this.mcsProfile = mcsProfile;
        this.compiler = CompilerResolver.resolve(config);
    }

    public List<Diagnostic> lint(PackDefinition pack) {
        if (!config.lintBeforeCompile) {
            return List.of();
        }
        try {
            ProcessResult result = SubprocessRunner.run(
                    compiler.toProcessCommand(List.of("lint", "--json", pack.entryFile().toString())),
                    pack.folder(),
                    120
            );
            if (result.stdout().isBlank()) {
                if (!result.success()) {
                    return List.of(new Diagnostic(relative(pack, pack.entryFile()), 1, 1, result.stderr().trim(), "error"));
                }
                return List.of();
            }
            List<Diagnostic> diagnostics = GSON.fromJson(result.stdout(), DIAGNOSTIC_LIST);
            return diagnostics == null ? List.of() : diagnostics;
        } catch (Exception error) {
            return List.of(new Diagnostic(relative(pack, pack.entryFile()), 1, 1, error.getMessage(), "error"));
        }
    }

    public List<Diagnostic> compile(PackDefinition pack) {
        try {
            if (Files.exists(pack.compiledFolder())) {
                deleteRecursive(pack.compiledFolder());
            }
        } catch (IOException error) {
            return List.of(new Diagnostic(pack.id(), 1, 1, error.getMessage(), "error"));
        }
        List<String> args = new ArrayList<>();
        args.add("compile");
        args.add("--mc-version");
        args.add(mcsProfile);
        args.add("--force");
        if (!config.verboseCompile) {
            args.add("--no-verbose");
        }
        args.add(pack.entryFile().toString());
        args.add(pack.displayName());
        args.add(McsPaths.compiledRoot().toString());
        try {
            ProcessResult result = SubprocessRunner.run(compiler.toProcessCommand(args), pack.folder(), 300);
            if (!result.success()) {
                String message = result.stderr().isBlank() ? result.stdout() : result.stderr();
                return List.of(new Diagnostic(relative(pack, pack.entryFile()), 1, 1, message.trim(), "error"));
            }
            return List.of();
        } catch (Exception error) {
            return List.of(new Diagnostic(relative(pack, pack.entryFile()), 1, 1, error.getMessage(), "error"));
        }
    }

    public List<Diagnostic> validateWithSpyglass(PackDefinition pack, String gameVersion) {
        if (!config.spyglassValidateAfterCompile || Files.notExists(pack.compiledFolder())) {
            return List.of();
        }
        try {
            Path script = McsPaths.spyglassScript();
            ProcessResult result = SubprocessRunner.run(
                    List.of(
                            "node",
                            script.toString(),
                            "--json",
                            "--mc-version",
                            gameVersion,
                            pack.compiledFolder().toString()
                    ),
                    null,
                    300
            );
            if (result.stdout().isBlank()) {
                if (!result.success()) {
                    return List.of(new Diagnostic(pack.id(), 1, 1, result.stderr().trim(), "error"));
                }
                return List.of();
            }
            List<Diagnostic> diagnostics = GSON.fromJson(result.stdout(), DIAGNOSTIC_LIST);
            return diagnostics == null ? List.of() : diagnostics;
        } catch (Exception error) {
            return List.of(new Diagnostic(pack.id(), 1, 1, error.getMessage(), "warning"));
        }
    }

    private static String relative(PackDefinition pack, Path file) {
        Path folder = pack.folder().toAbsolutePath().normalize();
        Path absolute = file.toAbsolutePath().normalize();
        if (!absolute.startsWith(folder)) {
            return absolute.toString().replace('\\', '/');
        }
        return folder.relativize(absolute).toString().replace('\\', '/');
    }

    private static void deleteRecursive(Path path) throws IOException {
        if (Files.isSymbolicLink(path)) {
            Files.delete(path);
            return;
        }
        if (Files.isDirectory(path)) {
            try (var stream = Files.list(path)) {
                var iterator = stream.iterator();
                while (iterator.hasNext()) {
                    deleteRecursive(iterator.next());
                }
            }
        }
        Files.deleteIfExists(path);
    }

}
