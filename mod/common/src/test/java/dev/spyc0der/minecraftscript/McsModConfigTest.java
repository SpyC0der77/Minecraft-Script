package dev.spyc0der.minecraftscript;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class McsModConfigTest {
    @TempDir
    Path tempDir;

    @Test
    void loadsDefaultsWhenConfigMissing() {
        McsModConfig config = McsModConfig.load(tempDir);

        assertEquals(McsModConfig.DEFAULT_COMMAND, config.pythonCommand());
        assertTrue(config.hotReload());
        assertTrue(config.hotReloadDisabledPacks().isEmpty());
        assertTrue(config.disabledPacks().isEmpty());
    }

    @Test
    void savesAndReloadsConfigValues() throws Exception {
        McsModConfig config = new McsModConfig(
                "python3 -m minecraft_script",
                false,
                Set.of("starter"),
                Set.of("custom")
        );
        config.save(tempDir);

        McsModConfig loaded = McsModConfig.load(tempDir);
        assertEquals("python3 -m minecraft_script", loaded.pythonCommand());
        assertFalse(loaded.hotReload());
        assertFalse(loaded.isHotReloadEnabledForPack("starter"));
        assertFalse(loaded.isHotReloadEnabledForPack("other"));
        assertFalse(loaded.isPackEnabled("custom"));
        assertTrue(loaded.isPackEnabled("starter"));
    }

    @Test
    void withPackEnabledUpdatesDisabledSet() {
        McsModConfig config = new McsModConfig(McsModConfig.DEFAULT_COMMAND, true, Set.of(), Set.of("starter"));

        McsModConfig enabled = config.withPackEnabled("starter", true);
        assertTrue(enabled.isPackEnabled("starter"));

        McsModConfig disabled = enabled.withPackEnabled("Custom", false);
        assertFalse(disabled.isPackEnabled("custom"));
    }
}
