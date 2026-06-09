package dev.spyc0der77.mcspacks.forge;

import dev.spyc0der77.mcspacks.McsPacks;
import net.minecraftforge.fml.common.Mod;

@Mod(McsPacksForge.MOD_ID)
public final class McsPacksForge {
    public static final String MOD_ID = "mcs_packs";

    public McsPacksForge() {
        McsPacks.init();
    }
}
