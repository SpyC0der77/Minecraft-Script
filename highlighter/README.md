# Minecraft Script Language Support

Language support for [Minecraft Script](https://github.com/SpyC0der77/Minecraft-Script) `.mcs` files in VS Code.

## Features

- **Syntax highlighting** for MCS keywords, selectors, resource locations, built-in helpers, text components, and `command()` strings
- **Hover help** for keywords, built-in functions, text component methods, and target selectors (`@a`, `@s`, …)
- **MCS syntax diagnostics** via the Python `minecraft_script lint` command (requires Python 3 with the package installed)
- **Autocomplete** for keywords, builtins, TextComponent methods, user-defined functions, and import paths
- **Command linting and completion** inside literal `command("...")` and `command('...')` calls via [Spyglass](https://github.com/SpyglassMC/Spyglass)
- **Version picker** for command validation across supported Minecraft releases

## Commands

| Command | Description |
| --- | --- |
| **Minecraft Script: Select Command Lint Version** | Choose the Minecraft version Spyglass uses for command validation |
| **Minecraft Script: Show Output** | Open the Minecraft Script output channel (useful if linting fails on first run) |

## Settings

| Setting | Default | Description |
| --- | --- | --- |
| `mcsHighlighter.minecraftVersion` | `1.21.2` | Minecraft version used when linting literal `command()` strings |
| `mcsHighlighter.pythonPath` | *(auto)* | Python executable for MCS syntax validation |
| `mcsHighlighter.lintSourcePath` | *(empty)* | Fallback file path for resolving relative imports in unsaved buffers |

The first Spyglass lint run downloads Minecraft command data from the network. Dynamic commands such as `command(myVar)` are skipped because their final text is not known in the editor.

MCS syntax validation runs `python -m minecraft_script lint --json --stdin`. Install the package with `pip install -e .` from the repository root, or use the npm CLI after installing `minecraft-script`.

## Spyglass

This extension uses Spyglass only for Minecraft command linting inside literal `command()` strings. It does not register `.mcs` files as `.mcfunction`, and it does not enable Spyglass diagnostics across the whole MCS document.

Spyglass is MIT licensed: [SpyglassMC/Spyglass](https://github.com/SpyglassMC/Spyglass).

## Development

To work on the extension locally:

1. Open the `highlighter/` folder in VS Code.
2. Run `bun install`.
3. Run `bun run build` (or press `F5` to build and launch an Extension Development Host).
4. Open a `.mcs` file in the Extension Development Host.

To package a `.vsix` without publishing:

```commandline
bun run package
```

See [contributors.md](../contributors.md) for the full Marketplace publishing flow.
