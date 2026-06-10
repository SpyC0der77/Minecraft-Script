import json
import sys

from . import debug_code
from .compiler import build_datapack
from .common import COMMON_CONFIG, version
from .config_utils import update_config, reset_config
from .lint import lint_code
from .version_config import breaking_changes_between, load_version_profile
from pathlib import Path


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
    
- compile <path> [<datapack name>] [<output path>]: compile the associated
mcs file into a datapack. The resulting datapack folder will be named after
the mcs file, unless a datapack name is specified. The output path argument
specifies where the datapack should be generated (default to current path).

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
    # Manage args & parameters:
    args = list(args)
    minecraft_version = None
    if "--minecraft-version" in args:
        version_index = args.index("--minecraft-version")
        if version_index + 1 >= len(args):
            print("No version specified after --minecraft-version.")
            exit(1)
        minecraft_version = args[version_index + 1]
        del args[version_index:version_index + 2]

    arg_count = len(args)
    if arg_count < 1:
        print("No path specified to compile.")
        exit()

    source_path = Path(args[0]).resolve()
    datapack_name: str = (
        "-".join(source_path.name.split(".")[:-1]).replace("_", " ").title()
        if arg_count < 2 else
        args[1]
    )
    output_path = (
        Path(COMMON_CONFIG["default_output_path"]).resolve()
        if arg_count < 3 else
        Path(args[2]).expanduser().resolve()
    )

    verbose = COMMON_CONFIG["verbose"]

    # Check if given paths are valid:
    if not source_path.is_file():
        print(f"Error: Could not find file at {args[0] !r}")
        exit(-1)

    if output_path.exists() and not output_path.is_dir():
        print(f"Error: Output path is not a directory ({str(output_path) !r})")
        exit(-1)

    output_path.mkdir(parents=True, exist_ok=True)

    # Build datapack
    with open(source_path, 'rt', encoding='utf-8') as mcs_file:
        code = mcs_file.read()

    previous_version = COMMON_CONFIG["minecraft_version"]
    if minecraft_version is not None:
        try:
            load_version_profile(minecraft_version)
        except FileNotFoundError as error:
            print(f"Error: {error}")
            exit(1)
        COMMON_CONFIG["minecraft_version"] = minecraft_version

    try:
        build_datapack(code, datapack_name, str(output_path), verbose, source_path=source_path)
    finally:
        COMMON_CONFIG["minecraft_version"] = previous_version


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
