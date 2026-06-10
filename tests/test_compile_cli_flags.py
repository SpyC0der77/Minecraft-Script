import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from minecraft_script.common import COMMON_CONFIG, module_folder


EXAMPLE = Path(module_folder).parent / "examples" / "starter_datapack.mcs"


@pytest.fixture
def build_output(tmp_path):
    output = tmp_path / "out"
    output.mkdir()
    return output


def test_compile_force_rebuilds_existing_output(build_output):
    first = subprocess.run(
        [
            sys.executable,
            "-m",
            "minecraft_script",
            "compile",
            "--force",
            "--mc-version",
            "1.21.11",
            "--no-verbose",
            str(EXAMPLE),
            "Starter Pack",
            str(build_output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert first.returncode == 0, first.stderr

    marker = build_output / "Starter Pack" / "pack.mcmeta"
    assert marker.is_file()
    marker.write_text('{"pack":{"pack_format":0,"description":"stale"}}', encoding="utf-8")

    second = subprocess.run(
        [
            sys.executable,
            "-m",
            "minecraft_script",
            "compile",
            "--force",
            "--mc-version",
            "1.21.11",
            "--no-verbose",
            str(EXAMPLE),
            "Starter Pack",
            str(build_output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert second.returncode == 0, second.stderr
    assert "stale" not in marker.read_text(encoding="utf-8")


def test_compile_mc_version_does_not_mutate_config(build_output):
    original_version = COMMON_CONFIG["minecraft_version"]
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "minecraft_script",
                "compile",
                "--force",
                "--mc-version",
                "1.21.11",
                "--no-verbose",
                str(EXAMPLE),
                "Starter Pack",
                str(build_output),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert COMMON_CONFIG["minecraft_version"] == original_version
        with open(f"{module_folder}/config.json", encoding="utf-8") as config_file:
            persisted_config = json.loads(config_file.read())
        assert persisted_config["minecraft_version"] == original_version
    finally:
        if build_output.exists():
            shutil.rmtree(build_output, ignore_errors=True)
