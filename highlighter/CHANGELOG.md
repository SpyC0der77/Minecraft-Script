# Change Log

All notable changes to the Minecraft Script Language Support extension are documented here.

## [0.1.0] - 2026-06-08

### Added

- MCS syntax and import diagnostics via the Python `minecraft_script lint` command
- Autocomplete for keywords, builtins, TextComponent methods, user-defined functions, and import paths
- Settings: `mcsHighlighter.pythonPath` and `mcsHighlighter.lintSourcePath`

## [0.0.1] - 2026-06-07

### Added

- Syntax highlighting for Minecraft Script (`.mcs`) files
- Hover documentation for keywords, built-in functions, text components, and target selectors
- Command linting, completion, and hover inside literal `command("...")` and `command('...')` strings via Spyglass
- Configurable Minecraft version for command validation (`mcsHighlighter.minecraftVersion`)
- Commands: **Minecraft Script: Select Command Lint Version** and **Minecraft Script: Show Output**
