# Minecraft Script

Minecraft Script is primarily a tool to make Minecraft Datapack creation easier. Minecraft Script is an interpreted programming language which goes through the Python interpreter for output. However, interpretation is not its main feature, and is rather more of a debugging tool, as its sole purpose is to allow you to validate your code before building it into a full datapack.

Be sure to check out the [documentation](https://github.com/SpyC0der77/Minecraft-Script/tree/main/documentation) and the provided [examples](https://github.com/SpyC0der77/Minecraft-Script/tree/main/examples)!

## Supported Versions


| Version Number | Development Status |
| -------------- | ------------------ |
| 1.21.2         | Continued Support  |
| 1.21.4         | Continued Support  |
| 1.21.5         | Continued Support  |
| 1.21.6         | Continued Support  |
| 1.21.7         | Continued Support  |
| 1.21.8         | Continued Support  |
| 1.21.9         | Continued Support  |
| 1.21.10        | Continued Support  |
| 1.21.11        | Continued Support  |
| 26.1           | Continued Support  |


## Installation

### npm (recommended)

Install the CLI through npm. This is a thin wrapper around the Python package and requires Python 3 and Git.

```commandline
npm install -g minecraft-script
```

On install, npm runs `pip install git+https://github.com/SpyC0der77/Minecraft-Script.git@v<version>` automatically when it can find Python. After that, use `mcs` or `minecraft-script` on your PATH:

```commandline
mcs help
mcs compile path/to/file.mcs
```

Or run it once without installing globally:

```commandline
npx minecraft-script compile path/to/file.mcs
```

Use `npx minecraft-script`, not bare `npx mcs` — there is an unrelated `mcs` package on npm.

### Python (from GitHub)

Install the Python package directly from this repository. Replace `@v<version>` with a [release tag](https://github.com/SpyC0der77/Minecraft-Script/tags) (for example `@v0.3.4`) or use `@main` for the latest commit.

```commandline
pip install git+https://github.com/SpyC0der77/Minecraft-Script.git@v<version>
```

Or clone the repo and install in editable mode for development:

```commandline
git clone https://github.com/SpyC0der77/Minecraft-Script.git
cd Minecraft-Script
pip install -e .
```

## Editor Support

The VS Code extension in `[highlighter/](highlighter/)` adds language support for `.mcs` files:

- Syntax highlighting based on JavaScript, with MCS-specific keywords, selectors, and resource locations
- Hover help for keywords, built-in functions, text component methods, and target selectors
- Command linting, hover, and autocompletion inside literal `command("...")` and `command('...')` strings via [Spyglass](https://github.com/SpyglassMC/Spyglass)

To try it locally:

1. Open the `highlighter/` folder in VS Code.
2. Run `bun install`.
3. Press `F5` to launch an Extension Development Host and open a `.mcs` file.

Use **Minecraft Script: Select Command Lint Version** from the command palette (Cmd or Ctrl + P) to choose the Minecraft version used for command validation. See `[highlighter/README.md](highlighter/README.md)` for more details.

## Using Minecraft Script to make Datapacks

### Debugging your program

To debug your program, you can first run your file like any other programming language.
To do this, use the following command:

```commandline
python -m minecraft_script debug <path>
```

*where `<path>` is a relative or absolute path to your `.mcs` file*

With npm installed globally, the equivalent is:

```commandline
mcs debug <path>
```

### Building your datapack

To actually build your minecraft datapack, which you can then simply drag & drop into your
minecraft worlds, use the following command:

```commandline
python -m minecraft_script compile <path>
```

*where `<path>` is a relative or absolute path to your `.mcs` file*

With npm installed globally, the equivalent is:

```commandline
mcs compile <path>
```

### More info

For a list of all shell commands, you can use the following command:

```commandline
python -m minecraft_script help
```

or, with npm:

```commandline
mcs help
```

If you want to simplify the usage of shell commands, you can check out [the installations page in the documentation](https://github.com/SpyC0der77/Minecraft-Script/blob/main/documentation/custom-installations.md).

### Configuration

Use `config set default_output_path <path>` to change the default compile output directory. The directory is created if it does not exist, and the resolved absolute path is stored in `config.json`. Existing relative values (such as the default `"."`) continue to work at compile time because `compile` resolves `default_output_path` again before use.

## GitHub

**[Link to GitHub Repository](https://github.com/SpyC0der77/Minecraft-Script)**

Source code, documentation, and examples can all be found on GitHub. Upstream development also continues at [Bard-Gaming/Minecraft-Script](https://github.com/Bard-Gaming/Minecraft-Script).

## Compatibility

This Python package runs on **Windows**, **macOS**, and **Linux**. You can pass file paths in either relative or absolute form using your platform's native separators. The npm wrapper requires **Node.js 18+** in addition to Python 3.