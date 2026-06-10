package dev.spyc0der.minecraftscript;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class McsPackWatcherTest {
    @Test
    void compileDelayWaitsForSettleAfterFirstChange() {
        assertEquals(150, McsPackWatcher.computeCompileDelayMillis(1_000, 1_000));
    }

    @Test
    void compileDelayShrinksAsMaxWaitApproaches() {
        assertEquals(150, McsPackWatcher.computeCompileDelayMillis(1_000, 1_100));
        assertEquals(50, McsPackWatcher.computeCompileDelayMillis(1_000, 1_350));
    }

    @Test
    void compileDelayFiresImmediatelyAfterMaxWait() {
        assertEquals(0, McsPackWatcher.computeCompileDelayMillis(1_000, 1_400));
        assertEquals(0, McsPackWatcher.computeCompileDelayMillis(1_000, 2_000));
    }
}
