"""Tests for the versioned build template files added/moved in this PR.

Covers:
- minecraft_script/compiler/build_templates/builtins/1.20.4/*.mcfunction
- minecraft_script/compiler/build_templates/math/1.20.4/*.mcfunction
- minecraft_script/compiler/build_templates/tags/1.20.4/block/no_collision.json
"""
import json
import os
from pathlib import Path

import minecraft_script.version_config as vc

TEMPLATES_BASE = Path(__file__).resolve().parents[1] / "minecraft_script" / "compiler" / "build_templates"
BUILTINS_1204 = TEMPLATES_BASE / "builtins" / "1.20.4"
MATH_1204 = TEMPLATES_BASE / "math" / "1.20.4"
TAGS_1204 = TEMPLATES_BASE / "tags" / "1.20.4"


# ===========================================================================
# Directory structure tests
# ===========================================================================

class TestVersionedDirectoryStructure:
    def test_builtins_1204_dir_exists(self):
        assert BUILTINS_1204.is_dir()

    def test_math_1204_dir_exists(self):
        assert MATH_1204.is_dir()

    def test_tags_1204_dir_exists(self):
        assert TAGS_1204.is_dir()

    def test_old_unversioned_builtins_dir_gone(self):
        old_path = TEMPLATES_BASE / "builtins" / "give_item.mcfunction"
        # The old file should no longer exist at unversioned path
        assert not old_path.is_file()

    def test_old_unversioned_math_dir_gone(self):
        # Old path was math/add.mcfunction — should not exist
        old_path = TEMPLATES_BASE / "math" / "add.mcfunction"
        assert not old_path.is_file()


# ===========================================================================
# give_item.mcfunction — key PR change (format changed)
# ===========================================================================

class TestGiveItemMcfunction:
    def setup_method(self):
        self.path = BUILTINS_1204 / "give_item.mcfunction"

    def test_file_exists(self):
        assert self.path.is_file()

    def test_file_starts_with_macro_prefix(self):
        content = self.path.read_text(encoding="utf-8")
        assert content.startswith("$give @s")

    def test_file_has_components_without_brackets(self):
        """New format uses $(components) directly without square brackets.

        Old format: $give @s $(item)[$(components)] $(count)
        New format: $give @s $(item)$(components) $(count)
        """
        content = self.path.read_text(encoding="utf-8").strip()
        assert "$(components)" in content
        # The old format wrapped components in square brackets
        assert "[$(components)]" not in content

    def test_file_has_item_placeholder(self):
        content = self.path.read_text(encoding="utf-8")
        assert "$(item)" in content

    def test_file_has_count_placeholder(self):
        content = self.path.read_text(encoding="utf-8")
        assert "$(count)" in content

    def test_file_exact_content(self):
        content = self.path.read_text(encoding="utf-8").strip()
        assert content == "$give @s $(item)$(components) $(count)"


# ===========================================================================
# Other builtin mcfunction files
# ===========================================================================

class TestBuiltinMcfunctions:
    EXPECTED_FILES = ["command.mcfunction", "give_item.mcfunction", "log.mcfunction", "set_block.mcfunction"]

    def test_all_expected_files_present(self):
        for fname in self.EXPECTED_FILES:
            assert (BUILTINS_1204 / fname).is_file(), f"Missing: {fname}"

    def test_command_mcfunction_not_empty(self):
        content = (BUILTINS_1204 / "command.mcfunction").read_text(encoding="utf-8")
        assert len(content.strip()) > 0

    def test_log_mcfunction_not_empty(self):
        content = (BUILTINS_1204 / "log.mcfunction").read_text(encoding="utf-8")
        assert len(content.strip()) > 0

    def test_set_block_mcfunction_contains_setblock_command(self):
        content = (BUILTINS_1204 / "set_block.mcfunction").read_text(encoding="utf-8")
        assert "setblock" in content.lower() or "$(block)" in content


# ===========================================================================
# Math mcfunction files
# ===========================================================================

class TestMathMcfunctions:
    EXPECTED_MATH_OPS = [
        "add", "subtract", "multiply", "divide", "modulus",
        "equals", "greater_than", "greater_equals_than",
        "less_than", "less_equals_than",
        "u_add", "u_subtract", "u_not",
    ]

    def test_all_math_files_present(self):
        for op in self.EXPECTED_MATH_OPS:
            path = MATH_1204 / f"{op}.mcfunction"
            assert path.is_file(), f"Missing math template: {op}.mcfunction"

    def test_add_uses_scoreboard_operation(self):
        content = (MATH_1204 / "add.mcfunction").read_text(encoding="utf-8")
        assert "scoreboard players operation" in content

    def test_add_uses_out_scoreboard(self):
        content = (MATH_1204 / "add.mcfunction").read_text(encoding="utf-8")
        assert ".out mcs_math" in content

    def test_add_uses_a_and_b_inputs(self):
        content = (MATH_1204 / "add.mcfunction").read_text(encoding="utf-8")
        assert ".a mcs_math" in content
        assert ".b mcs_math" in content

    def test_subtract_produces_subtraction(self):
        content = (MATH_1204 / "subtract.mcfunction").read_text(encoding="utf-8")
        assert "-=" in content

    def test_multiply_produces_multiplication(self):
        content = (MATH_1204 / "multiply.mcfunction").read_text(encoding="utf-8")
        assert "*=" in content

    def test_divide_produces_division(self):
        content = (MATH_1204 / "divide.mcfunction").read_text(encoding="utf-8")
        assert "/=" in content

    def test_modulus_produces_modulo(self):
        content = (MATH_1204 / "modulus.mcfunction").read_text(encoding="utf-8")
        assert "%=" in content

    def test_equals_uses_scoreboard_comparison(self):
        content = (MATH_1204 / "equals.mcfunction").read_text(encoding="utf-8")
        assert "scoreboard" in content

    def test_u_not_contains_not_logic(self):
        content = (MATH_1204 / "u_not.mcfunction").read_text(encoding="utf-8")
        # u_not should flip a boolean value
        assert "scoreboard" in content or "execute" in content

    def test_no_math_files_outside_versioned_folder(self):
        """Ensure math files are not duplicated at the unversioned level."""
        for op in self.EXPECTED_MATH_OPS:
            old_path = TEMPLATES_BASE / "math" / f"{op}.mcfunction"
            assert not old_path.is_file(), f"Unexpected file at unversioned path: {old_path}"


# ===========================================================================
# Tags — no_collision.json
# ===========================================================================

class TestNoCollisionTag:
    def setup_method(self):
        self.path = TAGS_1204 / "block" / "no_collision.json"

    def test_file_exists(self):
        assert self.path.is_file()

    def test_file_is_valid_json(self):
        content = self.path.read_text(encoding="utf-8")
        data = json.loads(content)
        assert isinstance(data, dict)

    def test_json_has_values_key(self):
        data = json.loads(self.path.read_text(encoding="utf-8"))
        assert "values" in data

    def test_values_is_list(self):
        data = json.loads(self.path.read_text(encoding="utf-8"))
        assert isinstance(data["values"], list)

    def test_includes_minecraft_air(self):
        data = json.loads(self.path.read_text(encoding="utf-8"))
        assert "minecraft:air" in data["values"]

    def test_includes_void_air(self):
        data = json.loads(self.path.read_text(encoding="utf-8"))
        assert "minecraft:void_air" in data["values"]

    def test_old_unversioned_no_collision_gone(self):
        old_path = TEMPLATES_BASE / "tags" / "block" / "no_collision.json"
        assert not old_path.is_file()


# ===========================================================================
# predefined_root() points to versioned dirs (integration)
# ===========================================================================

class TestPredefinedRootIntegration:
    def test_math_predefined_root_contains_add_mcfunction(self):
        root = vc.predefined_root("math", "1.20.4")
        assert (Path(root) / "add.mcfunction").is_file()

    def test_builtins_predefined_root_contains_give_item_mcfunction(self):
        root = vc.predefined_root("builtins", "1.20.4")
        assert (Path(root) / "give_item.mcfunction").is_file()

    def test_tags_predefined_root_contains_no_collision_json(self):
        root = vc.predefined_root("tags", "1.20.4")
        assert (Path(root) / "block" / "no_collision.json").is_file()