# MCS Packs Mod

Architectury mod for Fabric, Forge, and NeoForge. Watches `.minecraft/mcs_packs/<pack>/`, runs `mcs lint` → `mcs compile` → Spyglass validation, then hot-reloads into the active world.

## Requirements

- Java 21
- MCS installed (`pip install -e .` from this repo). The mod auto-detects `mcs`, `python -m minecraft_script`, or common Windows Python installs; launchers with a limited PATH (Modrinth, Prism, etc.) get a bundled `mcs-compile.cmd` fallback.
- Node.js on PATH (Spyglass post-compile validation; optional — disable in `config/mcs-packs.json`)

## Supported Minecraft versions

All MCS profiles from `minecraft_script/versions/index.json`:

| MCS profile | Minecraft versions |
| ----------- | ------------------ |
| `1.21.2` | 1.21.2 |
| `1.21.4` | 1.21.4 |
| `1.21.5` | 1.21.5 |
| `1.21.6` | 1.21.6 |
| `1.21.7-8` | 1.21.7, 1.21.8 |
| `1.21.9-10` | 1.21.9, 1.21.10 |
| `1.21.11` | 1.21.11 |
| `26.1` | 26.1 |

Build one profile:

```bash
cd mod
python scripts/apply_version.py 1.21.11
./gradlew :fabric:build -Pmcs_profile=1.21.11
```

Build every profile × loader (24 artifacts):

```bash
cd mod
python scripts/build_all.py
```

Build a single target:

```bash
python scripts/build_all.py --profile 1.21.4 --loader fabric
```

## Layout

```
.minecraft/
  config/mcs-packs.json
  mcs_packs/
    starter/pack.mcs
    my_pack/pack.mcs
    _compiled/
```

## Dev run (Fabric)

```bash
python scripts/apply_version.py 1.21.11
./gradlew :fabric:runClient -Pmcs_profile=1.21.11
```

Loader dependency versions live in `versions/manifest.json`. Update those pins when bumping Minecraft support.
