import json
import os.path
from pathlib import Path

from .common import COMMON_CONFIG, module_folder
from .version_config import list_supported_versions, load_version_profile


def _write_config() -> None:
    with open(f"{module_folder}/config.json", "wt", encoding="utf-8") as file:
        json.dump(COMMON_CONFIG, file, indent=4, ensure_ascii=False)
        file.write("\n")


def reset_config() -> None:
    index_path = Path(module_folder) / "versions" / "index.json"
    default_version = "1.20.4"
    if index_path.is_file():
        with index_path.open("rt", encoding="utf-8") as file:
            default_version = json.load(file).get("default", default_version)

    COMMON_CONFIG.clear()
    COMMON_CONFIG.update({
        "minecraft_version": default_version,
        "debug_comments": True,
        "verbose": True,
        "default_output_path": ".",
    })
    _write_config()


def update_config(setting: str, value: str) -> None:
    value_wrapper_fnc = config_value_wrapper[setting]
    py_value = value_wrapper_fnc(value, setting)
    COMMON_CONFIG[setting] = py_value
    _write_config()


def config_boolean_check(value: str, setting: str) -> bool:
    py_value = value.lower().capitalize()

    if py_value not in ('True', 'False'):
        print(f"Error: incorrect value {value !r} for setting {setting !r}")
        exit(-1)

    return eval(py_value)  # safe to eval here


def config_path_check(value: str, setting: str) -> str:
    path = value.replace("\\", "/")
    if not os.path.exists(path):
        print(f"Error: path {value !r} doesn't exist for setting {setting !r}")
        exit(-1)

    return path


def config_minecraft_version_check(value: str, setting: str) -> str:
    try:
        load_version_profile(value)
    except FileNotFoundError as error:
        supported = list_supported_versions()
        print(error)
        if supported:
            print(f"Supported versions: {', '.join(supported)}")
        exit(-1)
    return value


config_value_wrapper = {
    "minecraft_version": config_minecraft_version_check,
    "debug_comments": config_boolean_check,
    "verbose": config_boolean_check,
    "default_output_path": config_path_check,
}
