import json
import shutil
import sys

from . import debug_code
from .compiler import build_datapack
from .common import COMMON_CONFIG, version
from .config_utils import config_minecraft_version_check, temporary_config, update_config, reset_config
from .lint import lint_code
from .version_config import breaking_changes_between
from pathlib import Path


def _parse_flag_args(
    args: list,
    *,
    boolean_flags: set[str],
    value_flags: set[str],
) -> tuple[dict[str, str | bool], list[str]]:
    parsed: dict[str, str | bool] = {}
    positional: list[str] = []
    supported_flags = boolean_flags | value_flags
    index = 0
    while index < len(args):
        arg = args[index]
        if arg.startswith("--") and "=" in arg:
            flag, value = arg.split("=", 1)
            if flag in value_flags:
                parsed[flag] = value
                index += 1
                continue
        if arg in boolean_flags:
            parsed[arg] = True
            index += 1
            continue
        if arg in value_flags:
            next_arg = args[index + 1] if index + 1 < len(args) else None
            if next_arg is None or next_arg.startswith("--"):
                print(f"Error: {arg} requires a value.")
                exit(-1)
            parsed[arg] = next_arg
            index += 2
            continue
        if arg.startswith("--"):
            if arg not in supported_flags:
                print(f"Error: Unknown flag {arg}.")
                exit(-1)
            index += 1
            continue
        positional.append(arg)
        index += 1
    return parsed, positional


def _validate_datapack_name(datapack_name: str) -> None:
    if not datapack_name or datapack_name in {".", ".."}:
        print("Error: Invalid datapack name.")
        exit(-1)
    if ".." in datapack_name or "/" in datapack_name or "\\" in datapack_name:
        print("Error: Datapack name must not contain path separators or '..'.")
        exit(-1)


def handle_arguments(arguments: list):
    if not arguments:
        sh_default()

    function_name = arguments.pop(0)
    function = shell_functions.get(function_name)

    if function is not None:
        function(*arguments)

    else:
        print(f'Unknown MCS command: "{function_name}"')


sh_help_message = """
#-------------------------------HELP PAGE-------------------------------#
    
- help: displays this page!
    
- debug <path>: debug the minecraft script file found at the given path.
    
- compile [--mc-version <version>] [--force] [--verbose|--no-verbose] <path>
[<datapack name>] [<output path>]: compile the associated mcs file into a
datapack. --mc-version selects the Minecraft version profile without changing
config.json. --force deletes an existing output datapack folder before building.

- lint <path> [--json]: validate MCS syntax and imports for the given file.
Use --stdin to read code from standard input and pass --source <path> so
relative imports resolve correctly.

- config set <setting> <value>: Overwrite specified setting in config
to the new value. Use ``minecraft_version`` (e.g. ``1.20.4``) to select
which Minecraft version profile to compile for.

- config get [<setting>]: prints out specified settings' value. If no setting
is specified, all settings with their associated values will be shown.

- config default: Resets all config values to their default values.

#-----------------------------------------------------------------------#
"""


def sh_help(*args) -> None:
    print(sh_help_message)


def sh_default() -> None:
    print(
        f"Minecraft Script {version} (version {version}) \n"
        "Type \"help\" for more information."
    )
    exit()


def sh_debug(*args) -> None:
    if len(args) < 1:
        print("No path specified to debug.")
        exit()

    path: str = args[0]
    source_path = Path(path).resolve()

    with open(source_path, 'rt', encoding='utf-8') as file:
        code = file.read()
    debug_code(code, source_path=source_path)  # run code only after closing file


def sh_compile(*args) -> None:
    flags, positional = _parse_flag_args(
        list(args),
        boolean_flags={"--force", "--verbose", "--no-verbose"},
        value_flags={"--mc-version"},
    )
    if len(positional) < 1:
        print("No path specified to compile.")
        exit()

    source_path = Path(positional[0]).resolve()
    datapack_name: str = (
        "-".join(source_path.name.split(".")[:-1]).replace("_", " ").title()
        if len(positional) < 2 else
        positional[1]
    )
    output_path = (
        Path(COMMON_CONFIG["default_output_path"]).resolve()
        if len(positional) < 3 else
        Path(positional[2]).expanduser().resolve()
    )

    verbose = COMMON_CONFIG["verbose"]
    if "--verbose" in flags:
        verbose = True
    if "--no-verbose" in flags:
        verbose = False

    if not source_path.is_file():
        print(f"Error: Could not find file at {positional[0] !r}")
        exit(-1)

    if output_path.exists() and not output_path.is_dir():
        print(f"Error: Output path is not a directory ({str(output_path) !r})")
        exit(-1)

    output_path.mkdir(parents=True, exist_ok=True)
    resolved_output = output_path.resolve()

    _validate_datapack_name(datapack_name)

    datapack_folder = (resolved_output / datapack_name).resolve()
    if not datapack_folder.is_relative_to(resolved_output):
        print("Error: Datapack output path escapes output directory.")
        exit(-1)
    if "--force" in flags and datapack_folder.exists():
        if not datapack_folder.is_dir():
            print(f"Error: Output path is not a directory ({str(datapack_folder) !r})")
            exit(-1)
        shutil.rmtree(datapack_folder)

    overrides: dict[str, object] = {}
    if "--mc-version" in flags:
        mc_version = flags["--mc-version"]
        if not isinstance(mc_version, str) or mc_version is True:
            print("Error: --mc-version requires a value.")
            exit(-1)
        overrides["minecraft_version"] = config_minecraft_version_check(mc_version, "minecraft_version")
    if "--verbose" in flags:
        overrides["verbose"] = True
    if "--no-verbose" in flags:
        overrides["verbose"] = False

    with open(source_path, 'rt', encoding='utf-8') as mcs_file:
        code = mcs_file.read()

    with temporary_config(**overrides):
        build_datapack(code, datapack_name, str(output_path), verbose, source_path=source_path)


def sh_config(*args) -> None:
    arg_count = len(args)
    args = list(args)
    if arg_count < 1:
        print("Invalid arguments. Use the \"help\" command for more information.")
        exit()

    arg_literal = args.pop(0)

    if arg_literal in ("set", "get", "default"):
        eval(f"sh_config_{arg_literal}(args)")
    else:
        print(f"Invalid argument {arg_literal !r}. Use the \"help\" command for more information.")
        exit()


def sh_config_set(args: list) -> None:
    if len(args) < 2:
        print("Invalid arguments. Use the \"help\" command for more information.")
        exit()
    setting = args[0]
    value = args[1]

    if setting not in COMMON_CONFIG.keys():
        print(f"Unknown setting {setting !r}.")
        exit()

    if setting == "minecraft_version":
        try:
            changes = breaking_changes_between(COMMON_CONFIG["minecraft_version"], value)
        except FileNotFoundError:
            changes = []
        if changes:
            print(f"Breaking changes from {COMMON_CONFIG['minecraft_version']} to {value}:")
            for change_version, change in changes:
                summary = change.get("summary", str(change))
                print(f"- {change_version}: {summary}")
            print("Options:")
            print('- Acknowledged, change version')
            print("- No, don't change")
            acknowledgement = input("Choose an option: ")
            if acknowledgement != "Acknowledged, change version":
                print("Minecraft version was not updated.")
                exit(-1)

    update_config(setting, value)
    print(f"Updated setting {setting !r} to value {value !r}")


def sh_config_get(args: list) -> None:
    if len(args) < 1:
        print("Minecraft Script configuration:")
        for setting, value in COMMON_CONFIG.items():
            print(f"- {setting}: {value !r}")
        exit()

    setting = args[0]
    nonexistent = object()
    value: any = COMMON_CONFIG.get(setting, nonexistent)

    if value is nonexistent:
        print(f"Unknown setting {setting !r}.")
        exit()

    print(
        f"Setting {setting !r} has the following value: \n"
        f"{value !r}"
    )


def sh_lint(*args) -> None:
    use_json = "--json" in args
    use_stdin = "--stdin" in args
    filtered_args = [arg for arg in args if arg not in {"--json", "--stdin"}]

    source_path = None
    if "--source" in filtered_args:
        source_index = filtered_args.index("--source")
        if source_index + 1 >= len(filtered_args):
            print("No path specified after --source.")
            exit(1)
        source_path = Path(filtered_args[source_index + 1]).resolve()
        del filtered_args[source_index:source_index + 2]

    if use_stdin:
        code = sys.stdin.read()
        if source_path is None and filtered_args:
            source_path = Path(filtered_args[0]).resolve()
    else:
        if not filtered_args:
            print("No path specified to lint.")
            exit(1)

        source_path = Path(filtered_args[0]).resolve()
        if not source_path.is_file():
            print(f"Path {str(source_path)!r} does not exist.")
            exit(1)
        code = source_path.read_text(encoding="utf-8")

    display_path = str(source_path) if source_path is not None else "<stdin>"

    diagnostics = lint_code(code, source_path=source_path)
    if use_json:
        print(json.dumps([diagnostic.to_dict() for diagnostic in diagnostics]))
        exit(0 if not diagnostics else 1)

    if not diagnostics:
        print(f"{display_path}: no issues found")
        exit(0)

    for diagnostic in diagnostics:
        print(f"{display_path}:{diagnostic.line}:{diagnostic.column}: {diagnostic.message}")
    exit(1)


def sh_config_default(args: list) -> None:
    confirm = input("Reset whole config to default values? (Y/N): ").lower().strip(" ")
    if confirm != "y":
        return

    reset_config()
    print("Successfully reset config to its default state")


shell_functions = {
    'help': sh_help,
    'debug': sh_debug,
    'compile': sh_compile,
    'lint': sh_lint,
    'config': sh_config,
}
