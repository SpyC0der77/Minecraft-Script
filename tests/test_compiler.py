"""
Tests for changed parts of minecraft_script/compiler/compiler.py

Covers: Compiler.__init__ version context setup, function_path, version-aware
directory names, predefined_root for math/builtins/tags.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import minecraft_script.version_config as vc
from minecraft_script.version_config import init_version_context, predefined_root


# ---------------------------------------------------------------------------
# predefined_root (also tested in test_version_config, but compiler-focused)
# ---------------------------------------------------------------------------

class TestPredefinedRootForTemplates:
    def test_math_folder_exists_for_1204(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        path = predefined_root("math")
        assert os.path.isdir(path), f"Expected math template dir at {path}"

    def test_builtins_folder_exists_for_1204(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        path = predefined_root("builtins")
        assert os.path.isdir(path), f"Expected builtins template dir at {path}"

    def test_tags_folder_exists_for_1204(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        path = predefined_root("tags")
        assert os.path.isdir(path), f"Expected tags template dir at {path}"

    def test_math_folder_contains_mcfunction_files(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        path = predefined_root("math")
        files = os.listdir(path)
        assert any(f.endswith(".mcfunction") for f in files)

    def test_math_folder_contains_add(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        path = predefined_root("math")
        assert "add.mcfunction" in os.listdir(path)

    def test_builtins_folder_contains_give_item(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        path = predefined_root("builtins")
        assert "give_item.mcfunction" in os.listdir(path)

    def test_tags_folder_contains_block_dir(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        path = predefined_root("tags")
        assert "block" in os.listdir(path)

    def test_no_collision_json_in_tags_block(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        path = predefined_root("tags")
        block_path = os.path.join(path, "block")
        assert "no_collision.json" in os.listdir(block_path)


# ---------------------------------------------------------------------------
# Compiler.__init__ - version context and path setup
# ---------------------------------------------------------------------------

class TestCompilerInit:
    def _make_compiler(self):
        """Create a Compiler instance without touching the filesystem."""
        from minecraft_script.compiler.compiler import Compiler
        return Compiler(
            ast=[],
            datapack_name="Test Pack",
            output_path="/tmp",
            verbose=False,
        )

    def test_compiler_sets_function_dir(self):
        compiler = self._make_compiler()
        assert compiler.function_dir == "functions"

    def test_compiler_sets_function_tag_dir(self):
        compiler = self._make_compiler()
        assert compiler.function_tag_dir == "functions"

    def test_compiler_datapack_id_lowercased(self):
        compiler = self._make_compiler()
        assert compiler.datapack_id == "test_pack"

    def test_compiler_initialises_version_context(self):
        self._make_compiler()
        ctx = vc.get_version_context()
        assert ctx is not None
        assert ctx.datapack_id == "test_pack"

    def test_compiler_version_profile_is_1204(self):
        compiler = self._make_compiler()
        assert compiler.version.profile["minecraft_version"] == "1.20.4"

    def test_compiler_pack_format_is_41(self):
        compiler = self._make_compiler()
        assert compiler.version.pack_format == "41"


# ---------------------------------------------------------------------------
# Compiler.function_path
# ---------------------------------------------------------------------------

class TestCompilerFunctionPath:
    def _make_compiler(self):
        from minecraft_script.compiler.compiler import Compiler
        return Compiler(
            ast=[],
            datapack_name="My Pack",
            output_path="/out",
            verbose=False,
        )

    def test_function_path_no_parts(self):
        compiler = self._make_compiler()
        path = compiler.function_path()
        assert path == "/out/My Pack/data/my_pack/functions/"

    def test_function_path_single_part(self):
        compiler = self._make_compiler()
        path = compiler.function_path("init.mcfunction")
        assert path == "/out/My Pack/data/my_pack/functions/init.mcfunction"

    def test_function_path_multiple_parts(self):
        compiler = self._make_compiler()
        path = compiler.function_path("user_functions", "main.mcfunction")
        assert path == "/out/My Pack/data/my_pack/functions/user_functions/main.mcfunction"

    def test_function_path_uses_function_dir(self):
        compiler = self._make_compiler()
        path = compiler.function_path("foo")
        # With 1.20.4, function_dir == "functions"
        assert "/functions/" in path

    def test_function_path_includes_datapack_id(self):
        compiler = self._make_compiler()
        path = compiler.function_path("bar")
        assert "/my_pack/" in path


# ---------------------------------------------------------------------------
# Build template files - mcfunction file content checks
# ---------------------------------------------------------------------------

class TestBuildTemplateFiles:
    """Ensure the moved .mcfunction files have the expected content."""

    def _read_template(self, category: str, filename: str) -> str:
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        path = os.path.join(predefined_root(category), filename)
        with open(path, "r") as f:
            return f.read()

    def test_give_item_mcfunction_uses_give_command(self):
        content = self._read_template("builtins", "give_item.mcfunction")
        assert "give" in content.lower()

    def test_give_item_mcfunction_references_item_and_count(self):
        content = self._read_template("builtins", "give_item.mcfunction")
        assert "$(item)" in content
        assert "$(count)" in content

    def test_give_item_new_format_uses_components_without_brackets(self):
        content = self._read_template("builtins", "give_item.mcfunction")
        # New format: $(components)$(count) without [brackets]
        assert "[$(components)]" not in content

    def test_add_mcfunction_uses_scoreboard(self):
        content = self._read_template("math", "add.mcfunction")
        assert "scoreboard" in content

    def test_command_mcfunction_exists(self):
        path = os.path.join(predefined_root("builtins"), "command.mcfunction")
        assert os.path.isfile(path)

    def test_log_mcfunction_exists(self):
        path = os.path.join(predefined_root("builtins"), "log.mcfunction")
        assert os.path.isfile(path)

    def test_set_block_mcfunction_exists(self):
        path = os.path.join(predefined_root("builtins"), "set_block.mcfunction")
        assert os.path.isfile(path)

    def test_no_collision_json_is_valid_json(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        import json
        path = os.path.join(predefined_root("tags"), "block", "no_collision.json")
        with open(path) as f:
            data = json.load(f)
        assert "values" in data or "replace" in data or len(data) > 0

    def test_math_template_files_present(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        math_path = predefined_root("math")
        expected_ops = {
            "add", "subtract", "multiply", "divide", "modulus",
            "equals", "greater_than", "less_than",
            "greater_equals_than", "less_equals_than",
            "u_add", "u_subtract", "u_not",
        }
        files_in_dir = {f.replace(".mcfunction", "") for f in os.listdir(math_path)}
        assert expected_ops.issubset(files_in_dir), (
            f"Missing math ops: {expected_ops - files_in_dir}"
        )