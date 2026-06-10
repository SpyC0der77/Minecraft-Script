package dev.spyc0der.minecraftscript;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

class McsCommandLineTest {
    @Test
    void keepsQuotedCommandPathTogether() {
        assertEquals(
                List.of("C:/Program Files/Python/python.exe", "-m", "minecraft_script"),
                McsCommandLine.split("\"C:/Program Files/Python/python.exe\" -m minecraft_script")
        );
    }

    @Test
    void splitsDefaultPythonModuleCommand() {
        assertEquals(
                List.of("python", "-m", "minecraft_script"),
                McsCommandLine.split("python -m minecraft_script")
        );
    }
}
