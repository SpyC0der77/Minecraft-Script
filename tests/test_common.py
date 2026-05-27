"""Tests for minecraft_script/common.py changes in this PR.

The PR replaced platform-specific module_folder detection with a
cross-platform pathlib-based approach.
"""
import os
from pathlib import Path

import minecraft_script.common as common_module


class TestModuleFolder:
    """Tests for the module_folder variable (changed from platform-specific to pathlib)."""

    def test_module_folder_is_string(self):
        assert isinstance(common_module.module_folder, str)

    def test_module_folder_is_absolute_path(self):
        assert os.path.isabs(common_module.module_folder)

    def test_module_folder_exists(self):
        assert os.path.isdir(common_module.module_folder)

    def test_module_folder_contains_config_json(self):
        config_path = os.path.join(common_module.module_folder, "config.json")
        assert os.path.isfile(config_path)

    def test_module_folder_points_to_minecraft_script_package(self):
        # The folder should be the minecraft_script package directory
        folder_name = os.path.basename(common_module.module_folder)
        assert folder_name == "minecraft_script"

    def test_module_folder_matches_pathlib_calculation(self):
        # Verify the value matches what the new code computes
        expected = str(Path(common_module.__file__).resolve().parent)
        assert common_module.module_folder == expected

    def test_module_folder_does_not_contain_backslashes_on_non_windows(self):
        # The old code joined with '/' explicitly; pathlib should give OS-native separator
        # On Linux/macOS this means no backslashes
        if os.name != "nt":
            assert "\\" not in common_module.module_folder

    def test_module_folder_does_not_end_with_separator(self):
        # Should not have trailing slash
        assert not common_module.module_folder.endswith(os.sep)
        assert not common_module.module_folder.endswith("/")


class TestCommonConfig:
    """Tests that COMMON_CONFIG is loaded correctly using the new module_folder."""

    def test_common_config_is_dict(self):
        assert isinstance(common_module.COMMON_CONFIG, dict)

    def test_common_config_has_minecraft_version(self):
        assert "minecraft_version" in common_module.COMMON_CONFIG

    def test_common_config_minecraft_version_is_string(self):
        assert isinstance(common_module.COMMON_CONFIG["minecraft_version"], str)

    def test_common_config_has_debug_comments(self):
        assert "debug_comments" in common_module.COMMON_CONFIG

    def test_common_config_has_verbose(self):
        assert "verbose" in common_module.COMMON_CONFIG

    def test_common_config_has_default_output_path(self):
        assert "default_output_path" in common_module.COMMON_CONFIG


class TestGenerateUuid:
    """Tests for generate_uuid() (unchanged but used throughout the module)."""

    def test_returns_string(self):
        uuid = common_module.generate_uuid()
        assert isinstance(uuid, str)

    def test_returns_unique_values(self):
        uuids = {common_module.generate_uuid() for _ in range(100)}
        assert len(uuids) == 100

    def test_uuid_format(self):
        uuid = common_module.generate_uuid()
        # UUID4 has 32 hex chars + 4 dashes = 36 chars total
        assert len(uuid) == 36
        parts = uuid.split("-")
        assert len(parts) == 5