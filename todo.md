# MCS Todo list

## Infrastructure
- [x] Add GitHub Actions CI (pytest + example compiles to `build_test/`)
- [x] Enable GitHub Issues on the fork for user bug reports
- [x] Add release automation notes or scripts for npm + GitHub tags

## Developer Experience
- [x] Align `config set default_output_path` with `compile` (auto-create missing directories)
- [x] Publish VS Code extension (`highlighter/`) to the Marketplace
- [x] Add highlighter CI build check

## Language / Compiler
- [ ] Track Minecraft version updates and refresh version profiles as needed
- [ ] Expand test coverage for lexer/parser edge cases

## Documentation
- [x] Finish syntax documentation
- [x] Finish data types documentation
- [x] Add a contributor guide (local setup, test compile to `build_test/`, release flow)

## Completed (v0.3.x)

### Lexer
- [x] Add async while loop (keyword)
- [x] Make entity selector work in lexer instead of parser
- [x] Fix entity selector not supporting spaces

### Parser
- [x] Add async while loop (variant to normal while loop)
- [x] Update entity selector

### Interpreter
- [x] Add async while loop (exact same as normal while loop)

### Compiler
- [x] Add async while loop (uses a function subscribed to tick.mcfunction)

### Shell Commands
- [x] Update ``compile`` command
  - [x] Change args to \<path> \[\<datapack name>] \[\<output path>]
  - [x] Added errors in case a path doesn't exist
- [x] Add config for verbose option
- [x] Add config for default output path
- [x] Add ``config default`` command to reset config to default (needs confirmation)
