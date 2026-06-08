# Minecraft Script

Minecraft Script is a tool to make Minecraft Datapack creation easier. Minecraft Script is an interpreted programming language which goes through the Python interpreter for output.

Be sure to check out the [documentation](https://github.com/SpyC0der77/Minecraft-Script/tree/main/documentation) and the provided [examples](https://github.com/SpyC0der77/Minecraft-Script/tree/main/examples)!

Special thanks to the [Spyglass](https://github.com/spyglassmc/spyglass) team for making an amazing VSCode extension for syntax highlighting, autocomplete for datapacks, and other useful datapack tools.

Of course, thanks to [Bard-Gaming](https://github.com/Bard-Gaming) for creating the original [Minecraft-Script project](https://github.com/Bard-Gaming/Minecraft-Script) that this fork is based on.

## Supported Versions


| Version Number | Development Status   | Version Profile                                        |
| -------------- | ------------------- | ------------------------------------------------------ |
| 1.21.2         | Continued Support   | [View](minecraft_script/versions/1.21.2.json)          |
| 1.21.4         | Continued Support   | [View](minecraft_script/versions/1.21.4.json)          |
| 1.21.5         | Continued Support   | [View](minecraft_script/versions/1.21.5.json)          |
| 1.21.6         | Continued Support   | [View](minecraft_script/versions/1.21.6.json)          |
| 1.21.7-8       | Continued Support   | [View](minecraft_script/versions/1.21.7-8.json)        |
| 1.21.9-10      | Continued Support   | [View](minecraft_script/versions/1.21.9-10.json)       |
| 1.21.11        | Continued Support   | [View](minecraft_script/versions/1.21.11.json)         |
| 26.1           | Continued Support   | [View](minecraft_script/versions/26.1.json)            |


## Installation

### npm (recommended)

Install the CLI through npm. This is a wrapper around the Python package and requires Python 3 and Git.

```commandline
npm install -g minecraft-script
```

After that, use `mcs` or `minecraft-script` on your PATH:

```commandline
mcs help
mcs compile path/to/file.mcs
```

Or run it once without installing globally:

```commandline
npx minecraft-script compile file.mcs
```

NOTE: Use `npx minecraft-script`, not bare `npx mcs` — there is an unrelated `mcs` package on npm.

### Pip (From GitHub)

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

## VSCode Language Support

The VS Code extension available in this repo at [highlighter/](highlighter/) and on the [VSCode Extension Marketplace](https://marketplace.visualstudio.com/items?itemName=SpyC0der77.minecraft-script-language-support) adds language support for `.mcs` files:

- Syntax highlighting based on JavaScript, with MCS-specific keywords, selectors, and resource locations
- Hover help for keywords, built-in functions, text component methods, and target selectors
- Command linting, hover, and autocompletion inside literal `command("...")` and `command('...')` strings via [Spyglass](https://github.com/SpyglassMC/Spyglass)

To try it locally:

1. Open the `highlighter/` folder in VS Code.
2. Run `bun install`.
3. Press `F5` to launch an Extension Development Host and open a `.mcs` file.

Use **Minecraft Script: Select Command Lint Version** from the command palette (Cmd+Shift+P / Ctrl+Shift+P) to choose the Minecraft version used for command validation. Install the [VS Code extension](https://marketplace.visualstudio.com/items?itemName=SpyC0der77.minecraft-script-language-support) from the Marketplace, or see [highlighter/README.md](highlighter/README.md) to run it locally.

## Using Minecraft Script to make Datapacks

### Debugging your program

To debug your program, you can first run your file like any other programming language.
To do this, use the following command:

```commandline
python -m minecraft_script debug <path>
```

*where `<path>` is a relative or absolute path to your `.mcs` file*

With the npm package installed globally, the equivalent is:

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

## Contributing

See [contributors.md](contributors.md) for local setup, testing, the release flow, and VS Code extension publishing.

## GitHub

**[Link to GitHub Repository](https://github.com/SpyC0der77/Minecraft-Script)**

Source code, documentation, and examples can all be found on GitHub.