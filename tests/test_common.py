"""
Tests for minecraft_script/common.py

Covers: module_folder (pathlib-based detection), generate_uuid, COMMON_CONFIG loading.
"""
import os
import re
from pathlib import Path

import pytest

from minecraft_script.common import module_folder, generate_uuid, COMMON_CONFIG, version


class TestModuleFolder:
    def test_module_folder_is_string(self):
        assert isinstance(module_folder, str)

    def test_module_folder_ends_with_minecraft_script(self):
        # The module lives in .../minecraft_script/
        assert module_folder.endswith("minecraft_script")

    def test_module_folder_is_absolute(self):
        assert os.path.isabs(module_folder)

    def test_module_folder_exists(self):
        assert os.path.isdir(module_folder)

    def test_module_folder_contains_config_json(self):
        assert os.path.isfile(os.path.join(module_folder, "config.json"))

    def test_module_folder_uses_pathlib(self):
        # Verify the path resolution matches what Path would give
        import minecraft_script.common as cm
        expected = str(Path(cm.__file__).resolve().parent)
        assert module_folder == expected

    def test_module_folder_is_cross_platform(self):
        # Should never contain raw backslashes on any platform
        # (pathlib normalises separators)
        assert "\\" not in module_folder or os.sep == "\\"


class TestGenerateUuid:
    def test_returns_string(self):
        assert isinstance(generate_uuid(), str)

    def test_returns_valid_uuid_format(self):
        uuid = generate_uuid()
        pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        )
        assert pattern.match(uuid), f"UUID {uuid!r} does not match expected format"

    def test_generates_unique_values(self):
        uuids = {generate_uuid() for _ in range(100)}
        assert len(uuids) == 100

    def test_uuid_length(self):
        # Standard UUID string: 32 hex chars + 4 dashes = 36 chars
        assert len(generate_uuid()) == 36


class TestCommonConfig:
    def test_config_is_dict(self):
        assert isinstance(COMMON_CONFIG, dict)

    def test_config_has_minecraft_version(self):
        assert "minecraft_version" in COMMON_CONFIG

    def test_config_has_debug_comments(self):
        assert "debug_comments" in COMMON_CONFIG

    def test_config_has_verbose(self):
        assert "verbose" in COMMON_CONFIG

    def test_config_has_default_output_path(self):
        assert "default_output_path" in COMMON_CONFIG

    def test_minecraft_version_is_string(self):
        assert isinstance(COMMON_CONFIG["minecraft_version"], str)


class TestVersion:
    def test_version_is_string(self):
        assert isinstance(version, str)

    def test_version_matches_semver_pattern(self):
        pattern = re.compile(r'^\d+\.\d+\.\d+$')
        assert pattern.match(version), f"Version {version!r} is not in semver format"