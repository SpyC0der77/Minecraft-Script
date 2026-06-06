# Minecraft Script Highlighter

VS Code language support for Minecraft Script `.mcs` files.

## Try It Locally

1. Open the `highlighter/` folder in VS Code.
2. Run `bun install` if you have not already.
3. Press `F5` to build and launch an Extension Development Host.
4. Open a `.mcs` file in the Extension Development Host.

If command linting fails, open the **Minecraft Script** output channel: in the Output panel, use the dropdown on the right (it may say "Tasks") and select **Minecraft Script**. You can also run **Minecraft Script: Show Output** from the command palette. The first run downloads Minecraft command data from the network.

The grammar highlights Minecraft Script-specific syntax such as `set`, `on`, selector-prefixed calls, event bindings, built-in helpers, text component chains, Minecraft resource locations, and `command()` strings. It still includes VS Code's JavaScript grammar as a fallback for JavaScript-like expressions.

The small command-name keyword list used inside `command()` strings targets the default `1.21.2` lint version. Full command validation comes from Spyglass and follows the version selected with `Minecraft Script: Select Command Lint Version`.

## Spyglass

This extension uses Spyglass only for Minecraft command linting inside literal `command("...")` and `command('...')` calls. It does not register `.mcs` files as `.mcfunction`, and it does not enable Spyglass diagnostics across the whole MCS document.

Dynamic command values such as `command(cmd)` are skipped because their final command text is not available to the editor.

Use the `Minecraft Script: Select Command Lint Version` command from the VS Code command menu to choose the Minecraft version used by Spyglass. The command updates `mcsHighlighter.minecraftVersion` and re-lints open `.mcs` files.

Spyglass is MIT licensed and available at [SpyglassMC/Spyglass](https://github.com/SpyglassMC/Spyglass). See `../spyglass/LICENSE` for the original license text and copyright notice.
