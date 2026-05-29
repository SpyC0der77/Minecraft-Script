# For Contributors
If you want to contribute, look here.

## Updating to new version of game
If you are trying to add compatibility for a new version of Minecraft, here is how you can do it.

 1. Find breaking changes from the [Datapack breaking changes](https://datapack.wiki/wiki/info/breaking-changes) page
 2. Copy `minecraft_script/versions/1.20.4.json` to `minecraft_script/versions/<version>.json`
 3. Update the `orchestration` section for datapack layout changes (folder names, `pack.mcmeta` format, function tags, MCS built-in feature paths). See the `breaking_changes` map in the JSON for which keys apply per game version.
 4. Update Handlebars `templates` only for compiler-generated command shapes (not user NBT in `.mcs` source).
 5. Copy `minecraft_script/compiler/build_templates/math/1.20.4/` (and `builtins/`, `tags/`) to matching `<version>/` folders; edit predefined `.mcfunction` files as needed
 6. Add the version to `minecraft_script/versions/index.json`
 7. Create PR to merge into main branch

Users switch versions with `config set minecraft_version <version>` (default is in `versions/index.json`).

### Orchestration vs user NBT

- **`orchestration`**: datapack folders, pack format, function tags, scoreboard names, MCS built-in feature wiring, and **`orchestration.commands`** (all `execute` / scoreboard patterns for if/while/for, math, raycast, etc.).
- **`template_assemblies`**: lists which command paths to stitch for each compiler template key (e.g. `control.if.branch`).
- **User `.mcs` files**: item NBT, `/give` components, entity data in `command()` strings — authors update those when the game changes; the compiler does not rewrite them.
