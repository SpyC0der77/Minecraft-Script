# For Contributors
If you want to contribute, look here.

## Updating to new version of game
If you are trying to add compatibility for a new version of Minecraft, here is how you can do it.

 1. Find breaking changes from [HERE](https://datapack.wiki/wiki/info/breaking-changes)
 2. Copy `minecraft_script/versions/1.20.4.json` to `minecraft_script/versions/<version>.json` and update Handlebars templates
 3. Copy `minecraft_script/compiler/build_templates/math/1.20.4/` (and `builtins/`, `tags/`) to matching `<version>/` folders; edit predefined `.mcfunction` / tag files as needed
 4. Add the version to `minecraft_script/versions/index.json`
 5. Create PR to merge into main branch

Users switch versions with `config set minecraft_version <version>` (default is in `versions/index.json`).
