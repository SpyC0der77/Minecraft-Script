package dev.spyc0der77.mcspacks.util;

import java.io.IOException;
import java.nio.file.Path;

public final class SafePaths {
    private SafePaths() {
    }

    public static void validateSafeName(String name) throws IOException {
        if (name == null || name.isBlank()) {
            throw new IOException("Name must not be blank");
        }
        if (name.equals(".") || name.contains("/") || name.contains("\\") || name.contains("..")) {
            throw new IOException("Unsafe path name: " + name);
        }
    }

    public static Path resolveChild(Path parent, String childName) throws IOException {
        validateSafeName(childName);
        Path normalizedParent = parent.toAbsolutePath().normalize();
        Path resolved = normalizedParent.resolve(childName).normalize();
        if (resolved.equals(normalizedParent) || !resolved.startsWith(normalizedParent)) {
            throw new IOException("Path escapes parent directory: " + childName);
        }
        return resolved;
    }
}
