package dev.spyc0der77.mcspacks.config;

public class ModConfig {
    public String compiler = "auto";
    public String compilerPath = "";
    public int debounceMs = 500;
    public boolean autoReload = true;
    public boolean verboseCompile = false;
    public String minecraftVersion = "auto";
    public boolean lintBeforeCompile = true;
    public boolean spyglassValidateAfterCompile = true;
    public boolean blockCompileOnLintErrors = true;
    public boolean blockReloadOnSpyglassErrors = true;
}
