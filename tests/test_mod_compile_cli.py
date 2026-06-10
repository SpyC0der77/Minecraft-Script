import json
from pathlib import Path

import pytest

from minecraft_script.common import COMMON_CONFIG
from minecraft_script import shell_commands


STARTER_PACK_SOURCE = """
function init() {
    tellraw("@a", text().text("MCS Starter Pack Loaded"));
}

function main() {
}
"""


def test_compile_minecraft_version_flag_does_not_persist_config(tmp_path, monkeypatch):
    source = tmp_path / "pack.mcs"
    output = tmp_path / "out"
    source.write_text(STARTER_PACK_SOURCE, encoding="utf-8")

    monkeypatch.setitem(COMMON_CONFIG, "minecraft_version", "1.21.2")

    shell_commands.sh_compile(
        str(source),
        "Flag Version Pack",
        str(output),
        "--minecraft-version",
        "1.21.11",
    )

    pack = json.loads((output / "Flag Version Pack" / "pack.mcmeta").read_text(encoding="utf-8"))["pack"]
    assert pack["min_format"] == [94, 1]
    assert COMMON_CONFIG["minecraft_version"] == "1.21.2"


@pytest.mark.parametrize(
    "minecraft_version",
    [
        "1.21.2",
        "1.21.4",
        "1.21.5",
        "1.21.6",
        "1.21.7",
        "1.21.8",
        "1.21.9",
        "1.21.10",
        "1.21.11",
    ],
)
def test_mod_starter_pack_compiles_for_mod_supported_versions(
    minecraft_version,
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "pack.mcs"
    output = tmp_path / "out"
    source.write_text(STARTER_PACK_SOURCE, encoding="utf-8")

    monkeypatch.setitem(COMMON_CONFIG, "minecraft_version", "1.21.2")

    shell_commands.sh_compile(
        str(source),
        f"Starter {minecraft_version}",
        str(output),
        "--minecraft-version",
        minecraft_version,
    )

    assert (output / f"Starter {minecraft_version}" / "pack.mcmeta").is_file()
