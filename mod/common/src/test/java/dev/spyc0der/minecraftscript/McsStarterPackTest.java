package dev.spyc0der.minecraftscript;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class McsStarterPackTest {
    @Test
    void packSourceIncludesHelloMessage() {
        assertTrue(McsStarterPack.packSource("Demo").contains("Hello from Demo"));
    }

    @Test
    void rejectsInvalidPackNames() {
        assertFalse(McsStarterPack.isValidPackName(""));
        assertFalse(McsStarterPack.isValidPackName("bad/name"));
        assertTrue(McsStarterPack.isValidPackName("My Pack"));
    }
}
