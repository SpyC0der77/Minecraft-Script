package dev.spyc0der.minecraftscript;

import java.nio.file.Path;

public interface McsServerAccess {
    Path saveRoot();

    String minecraftVersion();

    void executeReload();

    void notifyOperators(String message);
}
