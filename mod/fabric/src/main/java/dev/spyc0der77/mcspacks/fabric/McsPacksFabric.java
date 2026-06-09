package dev.spyc0der77.mcspacks.fabric;

import dev.spyc0der77.mcspacks.McsPacks;
import net.fabricmc.api.ModInitializer;

public final class McsPacksFabric implements ModInitializer {
    @Override
    public void onInitialize() {
        McsPacks.init();
    }
}
