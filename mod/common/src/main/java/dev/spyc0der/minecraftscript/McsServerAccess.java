package dev.spyc0der.minecraftscript;

import java.nio.file.Path;

public interface McsServerAccess {
    Path saveRoot();

    Path serverDirectory();

    String minecraftVersion();

    void executeReload();

    void executeStartupReload();

    void notifyOperators(String message);
}
