package dev.spyc0der77.mcspacks.neoforge;

import dev.spyc0der77.mcspacks.McsPacks;
import net.neoforged.fml.common.Mod;

@Mod(McsPacksNeoForge.MOD_ID)
public final class McsPacksNeoForge {
    public static final String MOD_ID = "mcs_packs";

    public McsPacksNeoForge() {
        McsPacks.init();
    }
}
