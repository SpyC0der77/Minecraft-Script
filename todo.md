# MCS Hot-Reload Mod — Implementation Todo

A cross-loader Minecraft mod (Fabric, Forge, NeoForge) that adds an `mcs_packs` folder to the game directory, compiles `.mcs` files on save, and hot-reloads the resulting datapacks into the running world.

**Target Minecraft versions** (from `minecraft_script/versions/index.json`):

| MCS profile   | Minecraft versions        |
| ------------- | ------------------------- |
| `1.21.2`      | 1.21.2                    |
| `1.21.4`      | 1.21.4                    |
| `1.21.5`      | 1.21.5                    |
| `1.21.6`      | 1.21.6                    |
| `1.21.7-8`    | 1.21.7, 1.21.8            |
| `1.21.9-10`   | 1.21.9, 1.21.10           |
| `1.21.11`     | 1.21.11                   |
| `26.1`        | 26.1                      |

---

## Core loop

1. Watch `mcs_packs/<pack>/` for `.mcs` file changes (create / modify / delete).
2. On update → **lint first**, then compile only if lint passes:
   ```bash
   mcs lint --json <path/to/changed.mcs>
   ```
   Surface diagnostics in chat (`[MCS] my_pack/pack.mcs:12:3 — expected '}'`). On lint **errors**, skip compile and keep the last good datapack.
3. On lint OK → delete `mcs_packs/_compiled/<pack>/` if it exists, then run MCS compile:
   ```bash
   mcs compile <path/to/mcs_packs/my_pack/pack.mcs> <pack_name> <path/to/mcs_packs/_compiled>
   ```
   Fallback if `mcs` is not on PATH:
   ```bash
   python -m minecraft_script compile <path/to/mcs_packs/my_pack/pack.mcs> <pack_name> <path/to/mcs_packs/_compiled>
   ```
4. On compile success → run **Spyglass** on the compiled datapack folder:
   ```bash
   node mcs-spyglass-validate.mjs --json --mc-version <game_version> <path/to/mcs_packs/_compiled/my_pack>
   ```
   Spyglass validates generated `.mcfunction` files, tags, JSON, and commands (uses `pack.mcmeta` + game version). Surface diagnostics in chat (`[Spyglass] my_pack/data/.../main.mcfunction:3:1 — …`).
5. On Spyglass **errors** → do **not** hot-reload; keep the last good injected datapack. Compiled output stays in `_compiled/` for fixing.
6. On Spyglass OK → inject / refresh the datapack and hot-reload into the running world.
7. On compile failure → log the error, keep the last good datapack loaded.

Pipeline: `mcs lint` → `mcs compile` → **Spyglass on output** → reload.

---

## Phase 0 — Research & Decisions

- [x] **Choose multi-loader scaffolding** — **Architectury**
  - Use [Architectury](https://architectury.dev/) with a shared `common` module and thin Fabric / Forge / NeoForge entrypoints.
  - Gradle layout: `mod/common`, `mod/fabric`, `mod/forge`, `mod/neoforge` (monorepo subfolder).
  - Build tooling: Architectury Plugin + Architectury Loom; platform-specific hooks live in loader modules, shared logic in `common`.

- [x] **Compiler integration** — subprocess `mcs compile`
  - MCS is Python; the mod shells out to the existing CLI on every file update.
  - Primary: `mcs compile <path> <name> <output>` (npm global install).
  - Fallback: `python -m minecraft_script compile <path> <name> <output>` (pip / editable install).
  - Set `minecraft_version` to match the running game before compile (env var or temp config — see Phase 3).
  - Delete `_compiled/<pack>/` before each compile (`Compiler.build()` fails if the output folder already exists).

- [x] **Lint & validate pipeline**
  - **Before compile:** `mcs lint --json` on changed `.mcs` files (syntax + imports). Errors block compile; show line/column in chat.
  - **After compile:** Spyglass validates the full compiled datapack in `_compiled/<pack>/` (mcfunctions, tags, JSON). Errors block hot-reload; show file/line in chat.

- [x] **`mcs_packs` layout and output flow**
  - Each pack is a **folder** under `mcs_packs/`. Mod config lives in the normal **`config/`** folder (not inside `mcs_packs/`).
    ```
    .minecraft/
      config/
        mcs-packs.json       # mod config (compiler path, debounce, auto-reload, etc.)
      mcs_packs/
        my_pack/             # one folder per datapack project
          pack.mcs           # entry point (default name; override in pack.json)
          helpers.mcs          # optional additional sources / imports
          pack.json            # optional per-pack overrides (display name, entry file)
        starter/
          pack.mcs
        _compiled/           # mod-managed build output (gitignored by users)
          my_pack/           # compiled datapack folder
          starter/
    ```
  - On save: any `.mcs` change inside `mcs_packs/my_pack/` recompiles that pack → `_compiled/my_pack/`.
  - Compile working directory: the pack folder (so relative imports between files in the same pack resolve).
  - On reload: inject `_compiled/*` into the active world's datapack list (not copy into `saves/<world>/datapacks/` — avoids stale duplicates and `/reload` disable issues).

- [ ] **Define hot-reload semantics**
  - **Lint / compile failure:** keep previous good datapack loaded; surface error in chat + log.
  - **Compile success + Spyglass errors:** compiled files remain on disk but are **not** injected/reloaded until Spyglass passes.
  - **Compile success + Spyglass OK:** replace datapack source in the mod's `PackRepository` entry, then trigger a datapack reload.
  - **Reload scope:** prefer targeted datapack reload over full `/reload` (preserves entities, reduces lag). Fall back to `/reload` if no stable internal API exists for a given loader version.
  - **Dedicated server:** only reload when source files change on disk (no "save" event from an editor on the server machine unless files are synced).

- [ ] **Map loader + MC version matrix**
  - 8 MCS profiles × 3 loaders = up to 24 published artifacts per release.
  - Use a version table in Gradle (similar to `minecraft_script/versions/index.json`) as the single source of truth for mod build targets.
  - Confirm minimum loader versions per MC release (Fabric Loader, Forge, NeoForge).

---

## Phase 1 — Project Scaffolding

- [ ] Create `mod/` Gradle multi-project:
  ```
  mod/
    build.gradle
    settings.gradle
    gradle.properties
    common/          # loader-agnostic logic
    fabric/          # Fabric entrypoint + platform hooks
    forge/           # Forge entrypoint + platform hooks
    neoforge/        # NeoForge entrypoint + platform hooks
  ```
- [ ] Configure Architectury Loom (or loader-specific Loom forks) for all three platforms.
- [ ] Add shared dependencies: SLF4J, Gson (config), optional Cloth Config for in-game settings UI.
- [ ] Wire CI job in `.github/workflows/` to build all matrix targets (can start with one MC version, expand later).
- [ ] Add `mod/README.md` with install instructions and `mcs_packs` usage (keep this todo as the engineering checklist).

---

## Phase 2 — `mcs_packs` Folder Lifecycle

- [ ] **Create folders on game launch**
  - Resolve game directory via loader API (`FabricLoader.getGameDir()`, Forge `FMLPaths.GAMEDIR`, etc.).
  - Create `mcs_packs/`, `mcs_packs/_compiled/`, and a starter pack folder `mcs_packs/starter/` with `pack.mcs` (from `examples/starter_datapack.mcs`) plus a short `mcs_packs/README.txt`.
  - Create default mod config in `config/` if missing (use loader config dir: `FabricLoader.getConfigDir()`, Forge `FMLPaths.CONFIGDIR`).

- [ ] **Load mod config from `config/mcs-packs.json`** (with defaults):
  ```json
  {
    "compiler": "auto",
    "compilerPath": "",
    "debounceMs": 500,
    "autoReload": true,
    "verboseCompile": false,
    "minecraftVersion": "auto",
    "lintBeforeCompile": true,
    "spyglassValidateAfterCompile": true,
    "blockCompileOnLintErrors": true,
    "blockReloadOnSpyglassErrors": true
  }
  ```
  - Lives in `.minecraft/config/` like every other mod — **not** inside `mcs_packs/`.
  - `compiler: "auto"` — try `mcs` on PATH, then `python -m minecraft_script`.
  - `minecraftVersion: "auto"` — derive from running game version, mapped through MCS profile aliases (`1.21.7` → `1.21.7-8` per `versions/index.json`).

- [ ] **Per-pack overrides** (optional `mcs_packs/<pack>/pack.json`):
  - Custom datapack display name, namespace override, `entryFile` if not default `pack.mcs`.

- [ ] **Discover packs**
  - Scan `mcs_packs/*/` subdirectories on startup (exclude `_compiled`).
  - Each subdirectory with a valid entry `.mcs` is one pack.
  - Build a `PackRegistry` map: `packFolder → entryMcs → compiledPath → packId`.

---

## Phase 3 — MCS Compiler Bridge

- [ ] **Implement `McsCompiler` service (common module)**
  - One method: `compile(Path mcsFile) → CompileResult`.
  - Runs `mcs compile` (or fallback) as a subprocess; capture stdout/stderr.
  - Working directory: the pack folder, e.g. `mcs_packs/my_pack/` (relative imports within a pack must resolve).
  - Before compile: delete `_compiled/<pack>/`.
  - After compile: return success/failure + output path.

- [ ] **Version mapping helper**
  - Ship `mcs-versions.json` (from `minecraft_script/versions/index.json`) in the mod JAR.
  - Map running game version → MCS profile (`1.21.8` → `1.21.7-8`).
  - Pass to compiler via env `MCS_MINECRAFT_VERSION` or temp config file.

- [ ] **Detect compiler on first run**
  - Probe: user `compilerPath` → `mcs` on PATH → `python -m minecraft_script`.
  - Error clearly if none found (link to MCS install docs).

- [ ] **Surface compile diagnostics**
  - Log subprocess output; show compile errors in chat + `logs/mcs-mod/latest.log`.

---

## Phase 3b — Lint & Spyglass Validate

- [ ] **Run `mcs lint --json` before each compile** (when `lintBeforeCompile` is true)
  - Lint the changed file; for entry-point compiles, also lint the entry `.mcs` after any sibling file in the pack changes.
  - Parse JSON diagnostics into `{ file, line, column, message, severity }`.
  - Chat format: `[MCS] my_pack/helpers.mcs:14:1 — Could not resolve import 'foo.mcs'`.
  - If `blockCompileOnLintErrors` and any error-severity diagnostic → skip compile, keep last good datapack.

- [ ] **Run Spyglass on compiled output after each successful compile** (when `spyglassValidateAfterCompile` is true)
  - Validate the datapack root: `mcs_packs/_compiled/<pack>/` (contains `pack.mcmeta`, `data/`, generated mcfunctions).
  - Build a headless CLI using `@spyglassmc/core` (same stack as `spyglass/` and `highlighter/`). Open the compiled folder as a Spyglass project; collect diagnostics on all files.
  - Spawn via Node: `node mcs-spyglass-validate.mjs --json --mc-version <version> <compiled_pack_dir>`.
  - Pass running game version (or read from `pack.mcmeta` + `mcs-versions.json` mapping). Optionally drop `spyglass.json` into `_compiled/<pack>/` with `env.gameVersion` if pack format alone is ambiguous.
  - Chat format: `[Spyglass] my_pack/data/<namespace>/function/....mcfunction:12:1 — Expected …`.
  - If `blockReloadOnSpyglassErrors` and any error-severity diagnostic → skip inject + reload; keep last good injected pack.
  - Warnings only → still reload (configurable later if needed).
  - Spyglass / Node unavailable → one-time chat warning; optionally allow reload without validation via config fallback.

- [ ] **Add `mcs-spyglass-validate.mjs` to repo** (e.g. under `mod/scripts/` or `npm/scripts/`)
  - JSON stdout: `[{ "file", "line", "column", "message", "severity" }]`.
  - Reuse Spyglass project init patterns from `highlighter/command-spyglass.mjs` / `spyglass` language server.

---

## Phase 4 — File Watcher → Compile on Update

- [ ] **Watch each `mcs_packs/<pack>/` folder for `.mcs` changes**
  - Java `WatchService` on a background thread; ignore `mcs_packs/_compiled/` and editor temp files.
  - A change to any `.mcs` in a pack folder triggers a recompile of that pack's entry file.

- [ ] **On any `.mcs` create/modify in a pack folder → lint → compile → Spyglass validate → reload**
  - Debounce per pack (`debounceMs` from `config/mcs-packs.json`, default 500 ms).
  - Cancel in-flight lint/compile/validate if the same pack changes again (generation counter).

- [ ] **On world load → compile all pack folders once**
  - Same code path as the watcher; ensures packs exist before first inject.

- [ ] **On pack folder delete (or entry `.mcs` removed) → remove `_compiled/<pack>/` and unregister datapack**

---

## Phase 5 — Datapack Injection & Hot Reload

- [ ] **Register compiled packs as dynamic datapack sources**
  - **Fabric:** `ResourceManagerHelper.registerBuiltinResourcePack(...)` or custom `PackResources` via `PackSource` / server pack repository hooks (verify against target Fabric API for 1.21.2+).
  - **Forge:** `AddPackFindersEvent` — add `PathPackResources` pointing at `_compiled/<pack>/`.
  - **NeoForge:** equivalent pack finder event (API renamed from Forge — confirm per version).
  - Assign a stable pack ID (e.g. `mcs_mod:<pack_name>`) and `PackSource.BUILT_IN` or a custom source so `/datapack list` shows them.

- [ ] **Implement `DatapackReloader` platform service**
  - `registerPack(Path compiledDir, String packName)`
  - `unregisterPack(String packName)`
  - `reloadDatapacks(MinecraftServer server)` — trigger reload on server thread.

- [ ] **Reload strategy (prefer least disruptive)**
  1. Try internal server reload API (`ReloadableServerResources`, `MinecraftServer.reloadResources`) with only datapack portion.
  2. If unavailable or unstable on a loader version, run `/reload` via server command source with OP bypass.
  3. Document side effects (function tags re-run, entities preserved vs. not) per approach.

- [ ] **Hook world lifecycle**
  - `SERVER_STARTED` → initial scan, compile, register, inject.
  - `SERVER_STOPPING` → stop watcher, clear injected packs.
  - Client disconnect / world unload — no reload needed.

- [ ] **Avoid conflict with MCS `kill.mcfunction`**
  - MCS kill template runs `datapack disable "file/{{datapackName}}"`. Injected packs are not `file/` packs — verify kill.mcfunction does not break hot-reload packs (may need MCS template tweak or mod-specific kill override in a future MCS release).

---

## Phase 6 — User Experience

- [ ] **In-game feedback**
  - Chat messages: `[MCS] Compiling my_pack…`, `[MCS] Reloaded 2 datapacks (1.2s)`, `[MCS] Compile failed: …`.
  - Optional action bar progress during compile + reload.

- [ ] **Keybind or command** (optional)
  - `/mcs reload` — force recompile all + reload.
  - `/mcs status` — show compiler path, watched files, last compile times.
  - `/mcs open` — open `mcs_packs/` folder in OS file manager.

- [ ] **Config screen** (Cloth Config / YACL)
  - Edits `config/mcs-packs.json` — compiler path, debounce, auto-reload toggle, verbose compile.

- [ ] **Log file**
  - `logs/mcs-mod/latest.log` with compile output for debugging.

---

## Phase 7 — MCS Repo Integration

- [ ] **Ship `mcs-versions.json` in mod JAR**
  - Generated at build time from `minecraft_script/versions/index.json` + profile `minecraft_version` fields.
  - Keeps mod in sync with MCS supported versions without manual duplication.

- [ ] **Add MCS CLI flags for mod use** (nice-to-have, not blocking v1)
  - `mcs compile --mc-version 1.21.11 --force <file.mcs> <name> <output>` — avoids mutating global `config.json` and handles output-dir cleanup in one step.
  - v1 workaround: mod deletes output dir itself before calling plain `mcs compile`.

- [ ] **Document workflow in main `readme.md`**
  - Section: "Live development with the MCS mod" — install mod, create a folder in `mcs_packs/` with a `pack.mcs`, edit & save, see changes in world.

- [ ] **Update `contributors.md`**
  - Mod build prerequisites (JDK 21, Gradle), run-client tasks per loader.

---

## Phase 8 — Version Matrix & Releases

- [ ] **Gradle version manifest** — one row per releasable artifact:
  | MC   | Fabric Loader | Forge | NeoForge | MCS profile |
  | ---- | ------------- | ----- | -------- | ----------- |
  | 1.21.2 | …           | …     | …        | 1.21.2      |
  | …    | …             | …     | …        | …           |
  | 26.1 | …             | …     | …        | 26.1        |

- [ ] **Build all targets** in CI; publish to Modrinth + CurseForge (optional).
- [ ] **Tag naming:** `mod-v0.1.0+1.21.11-fabric`, etc.
- [ ] **Compatibility policy:** mod major version tracks MCS major; declare minimum MCS / Python / Node version in mod metadata.

---

## Phase 9 — Testing

- [ ] **Manual test matrix** (per loader × at least 2 MC versions):
  - Fresh install creates `mcs_packs/`, `mcs_packs/starter/`, and `config/mcs-packs.json`.
  - Save `.mcs` inside a pack folder triggers lint → compile → Spyglass validate → reload; `load` function runs.
  - Lint, compile, or Spyglass errors keep previous injected pack active; chat shows diagnostic with file + line.
  - Spyglass catches bad commands in generated `.mcfunction` files that MCS lint missed.
  - Delete pack folder removes compiled output and unregisters datapack after reload.
  - Multi-pack: two pack folders compile and load independently.
  - Import between `.mcs` files within the same pack folder resolves correctly.

- [ ] **Automated tests (where feasible)**
  - Unit tests for version mapping (`1.21.10` → `1.21.9-10`).
  - Unit tests for debounce / watch event coalescing.
  - Integration test: invoke real `mcs compile` subprocess against `examples/starter_datapack.mcs` into `build_test/` (per `AGENTS.md`).
  - GameTest / gametest framework hooks for in-world verification (stretch goal).

- [ ] **Performance checks**
  - Compile + reload time for small vs. large packs.
  - No watcher thread leak on world unload.

---

## Phase 10 — Known Risks & Open Questions

- [ ] **Python / Node dependency** — v1 requires MCS installed separately (`npm install -g minecraft-script` or `pip install -e .`) **and Node on PATH** for post-compile Spyglass validation. Mod shows a clear error if `mcs` / `python -m minecraft_script` / Node is missing.
- [ ] **Dedicated server** — no automatic "save" unless using a sync tool; document that saves on the admin machine trigger reload.
- [ ] **`/reload` cost** — large packs may cause noticeable lag; targeted reload API needs per-version verification.
- [ ] **Pack format drift** — MCS `pack.mcmeta` templates must match the running MC version (handled by MCS version profiles if compiler gets correct `minecraft_version`).
- [ ] **Scoreboard / storage state** — reload re-runs `load.mcfunction`; user scripts must be idempotent or guard with scoreboard markers.
- [ ] **Multiplayer** — only operators / server-side compile should trigger reload; clients should not spawn compilers.
- [ ] **Security** — subprocess executes user-provided `.mcs` which compiles to mcfunctions; treat `mcs_packs/` as trusted local dev content only.

---

## Suggested Implementation Order

1. ~~Phase 0: Architectury scaffolding, subprocess `mcs compile`, `mcs_packs/` layout.~~
2. ~~Phase 1 — Architectury Gradle project (all MCS profiles × Fabric/Forge/NeoForge).~~
3. Phase 2 + 3 + 3b + 4 — `mcs_packs/` folder, file watcher, `mcs lint` → `mcs compile` → Spyglass validate on update.
4. Phase 5 — inject compiled output + hot-reload.
5. Phase 6 — chat/log feedback on compile success or failure.
6. Phase 8 — expand to all MCS versions + Forge + NeoForge.
7. Phase 7 + 9 — MCS CLI flags (optional), tests, release.

---

## Success Criteria

- [ ] Player installs mod, launches game, sees `mcs_packs/` and `config/mcs-packs.json` in `.minecraft/`.
- [ ] Saving `mcs_packs/starter/pack.mcs` triggers lint → compile → Spyglass validate within ~1–2 s.
- [ ] Spyglass errors in compiled output are shown in chat and **do not** hot-reload a broken pack.
- [ ] World reflects datapack changes without manual `/reload` or moving folders.
- [ ] Works on Fabric, Forge, and NeoForge for every MCS-supported Minecraft version listed above.
- [ ] Clear error when MCS is not installed; no silent failures.
