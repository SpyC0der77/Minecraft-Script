package dev.spyc0der77.mcspacks.deploy;

import java.io.IOException;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.BasicFileAttributes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.permissions.PermissionSet;
import net.minecraft.world.level.storage.LevelResource;

public final class DatapackDeployer {
    private DatapackDeployer() {
    }

    public static void syncPack(MinecraftServer server, Path compiledPack, String packFolderName) throws IOException {
        Path worldDatapacks = server.getWorldPath(LevelResource.DATAPACK_DIR);
        Files.createDirectories(worldDatapacks);
        Path target = worldDatapacks.resolve(packFolderName);
        if (Files.exists(target)) {
            deleteRecursive(target);
        }
        copyRecursive(compiledPack, target);
    }

    public static void reload(MinecraftServer server) {
        server.submit(() -> server.getCommands().performPrefixedCommand(
                server.createCommandSourceStack().withPermission(PermissionSet.ALL_PERMISSIONS),
                "reload"
        ));
    }

    private static void copyRecursive(Path source, Path target) throws IOException {
        Files.walkFileTree(source, new SimpleFileVisitor<>() {
            @Override
            public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs) throws IOException {
                Files.createDirectories(target.resolve(source.relativize(dir).toString()));
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                Path destination = target.resolve(source.relativize(file).toString());
                Files.createDirectories(destination.getParent());
                Files.copy(file, destination, StandardCopyOption.REPLACE_EXISTING);
                return FileVisitResult.CONTINUE;
            }
        });
    }

    private static void deleteRecursive(Path path) throws IOException {
        if (!Files.exists(path)) {
            return;
        }
        Files.walkFileTree(path, new SimpleFileVisitor<>() {
            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                Files.delete(file);
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult postVisitDirectory(Path dir, IOException exc) throws IOException {
                Files.delete(dir);
                return FileVisitResult.CONTINUE;
            }
        });
    }
}
