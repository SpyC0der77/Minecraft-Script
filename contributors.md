# For Contributors

This fork is maintained at [SpyC0der77/Minecraft-Script](https://github.com/SpyC0der77/Minecraft-Script). Upstream issues and PRs on [Bard-Gaming/Minecraft-Script](https://github.com/Bard-Gaming/Minecraft-Script) are not tracked here.

## Local setup

1. Clone the repository and install the Python package in editable mode:

```commandline
git clone https://github.com/SpyC0der77/Minecraft-Script.git
cd Minecraft-Script
pip install -e . -r requirements-dev.txt
```

2. Confirm the CLI works:

```commandline
python -m minecraft_script help
```

3. Optional — VS Code extension development (`highlighter/`):

```commandline
cd highlighter
bun install
bun run build
```

Open `highlighter/` in VS Code and press `F5` to launch an Extension Development Host.

## Running tests

From the repository root:

```commandline
pytest -q
```

CI runs the same suite on Python 3.10 and 3.12, plus a highlighter build check.

Tests that compile datapacks write output to `build_test/` at the repo root. That folder is gitignored and cleaned up automatically by pytest fixtures.

## Manual test compiles

When checking compiler output by hand, compile into `build_test/` instead of your Minecraft world folder:

```commandline
python -m minecraft_script compile examples/starter_datapack.mcs "Starter Datapack" build_test
```

Or with the npm CLI:

```commandline
mcs compile examples/starter_datapack.mcs "Starter Datapack" build_test
```

Inspect the generated datapack under `build_test/` before deleting it.

## Release flow

PyPI is not used for this fork — only the original upstream owner can publish the `minecraft-script` package there. Releases are distributed through **GitHub tags** and **npm**.

### Before you release

1. Merge changes to `main` and confirm CI is green.
2. Bump the version in both:
   - `pyproject.toml` (`[project].version`)
   - `npm/package.json` (`version`)
3. Verify the versions match:

```commandline
python scripts/check_release_versions.py
```

4. Commit the version bump (for example: `Release v0.3.5.`).

### Tag and GitHub release

```commandline
git tag v0.3.5
git push origin main
git push origin v0.3.5
```

Create a GitHub release from the tag on [SpyC0der77/Minecraft-Script/releases](https://github.com/SpyC0der77/Minecraft-Script/releases). Use the tag name as the release title (for example `v0.3.5`).

The npm wrapper installs the matching Python package with:

```commandline
pip install git+https://github.com/SpyC0der77/Minecraft-Script.git@v<version>
```

So the GitHub tag must exist before users install that npm version.

### Publish to npm

From the `npm/` directory:

```commandline
cd npm
npm publish
```

You must be logged in (`npm login`) and have publish access to the `minecraft-script` package on npm.

After publishing, users can install with:

```commandline
npm install -g minecraft-script
```

### Release checklist

- [ ] CI green on `main`
- [ ] `pyproject.toml` and `npm/package.json` versions match
- [ ] `python scripts/check_release_versions.py` passes
- [ ] Tag pushed (`v<version>`)
- [ ] GitHub release created from the tag
- [ ] `npm publish` from `npm/` succeeded

The VS Code extension (`highlighter/`) uses publisher **`SpyC0der77`** and is published to the Marketplace separately — see [Publishing the VS Code extension](#publishing-the-vs-code-extension).

## Publishing the VS Code extension

The highlighter lives in `highlighter/`. It is not published automatically with the Python/npm release.

### One-time setup

1. **Create a Marketplace publisher**
   - Go to [Visual Studio Marketplace publisher management](https://marketplace.visualstudio.com/manage).
   - Sign in with a Microsoft account.
   - Your publisher ID is **`SpyC0der77`** (must match `"publisher"` in `highlighter/package.json`).

2. **Create a Personal Access Token (PAT)**
   - Open [Azure DevOps](https://dev.azure.com/) → User settings → Personal access tokens.
   - Create a token with **Marketplace → Manage** scope.
   - Save the token somewhere safe; you only see it once.

3. **Install dependencies** (if you have not already):

```commandline
cd highlighter
bun install
```

Packaging metadata (`.vscodeignore`, `icon.png`, `CHANGELOG.md`, `LICENSE`, and `bun run package`) is already set up in the repo.

### Each release

1. Bump `"version"` in `highlighter/package.json` (semver, independent of the Python/npm `0.3.x` line).
2. Update `highlighter/CHANGELOG.md`.
3. Build, package, and smoke-test locally:

```commandline
cd highlighter
bun run package
```

Install the generated `.vsix` with **Extensions: Install from VSIX** in VS Code, or press `F5` in the `highlighter/` folder to test in the Extension Development Host.

4. Log in and publish:

```commandline
bunx vsce login SpyC0der77
bunx vsce publish --no-dependencies
```

When prompted for the PAT, paste the token from Azure DevOps.

5. Confirm the listing at [marketplace.visualstudio.com/items?itemName=SpyC0der77.minecraft-script-language-support](https://marketplace.visualstudio.com/items?itemName=SpyC0der77.minecraft-script-language-support).

### Updating an existing listing

Bump `highlighter/package.json` version, rebuild, and run `vsce publish` again. Marketplace users receive updates automatically through VS Code.

## Updating to a new version of Minecraft

If you are trying to add compatibility for a new version of Minecraft, here is how you can do it.

1. Find breaking changes from the [Datapack breaking changes](https://datapack.wiki/wiki/info/breaking-changes) page
2. Copy `minecraft_script/versions/1.21.2.json` to `minecraft_script/versions/<version>.json`
3. Update the `orchestration` section for datapack layout changes (folder names, `pack.mcmeta` format, function tags, MCS built-in feature paths). See the `breaking_changes` map in the JSON for which keys apply per game version.
4. Update Handlebars `templates` only for compiler-generated command shapes (not user NBT in `.mcs` source).
5. Copy `minecraft_script/compiler/build_templates/math/1.21.2/` (and `builtins/1.21.2/`, `tags/1.21.2/`) to matching `<version>/` folders; edit predefined `.mcfunction` files as needed
6. Add the version to `minecraft_script/versions/index.json`
7. Add the version to `highlighter/package.json` → `contributes.configuration.properties.mcsHighlighter.minecraftVersion.enum` if command linting should support it
8. Open a PR against `main`

Users switch versions with `config set minecraft_version <version>` (default is in `versions/index.json`).

### Orchestration vs user NBT

- **`orchestration`**: datapack folders, pack format, function tags, scoreboard names, MCS built-in feature wiring, and **`orchestration.commands`** (all `execute` / scoreboard patterns for if/while/for, math, raycast, etc.).
- **`template_assemblies`**: lists which command paths to stitch for each compiler template key (e.g. `control.if.branch`).
- **User `.mcs` files**: item NBT, `/give` components, entity data in `command()` strings — authors update those when the game changes; the compiler does not rewrite them.
