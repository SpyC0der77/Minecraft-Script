"""Tests for minecraft_script/version_config.py (new module added in this PR)."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import minecraft_script.version_config as vc
from minecraft_script import common


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

MINIMAL_PROFILE = {
    "minecraft_version": "0.0.test",
    "pack_format": 99,
    "paths": {
        "function_dir": "functions",
        "function_tag_dir": "functions",
    },
    "constants": {
        "testConst": "hello",
    },
    "templates": {
        "simple": "hello {{name}}",
        "multiline": "line1\nline2 {{value}}\nline3",
        "no_params": "static text",
        "with_const": "{{testConst}} world",
        "datapack_ref": "function {{datapack_id}}:something",
        "conditional": "{{#if flag}}yes{{else}}no{{/if}}",
    },
}


# ===========================================================================
# get_minecraft_version
# ===========================================================================

class TestGetMinecraftVersion:
    def test_returns_value_from_common_config(self):
        with patch.object(vc, "COMMON_CONFIG", {"minecraft_version": "1.20.4"}):
            assert vc.get_minecraft_version() == "1.20.4"

    def test_returns_different_version(self):
        with patch.object(vc, "COMMON_CONFIG", {"minecraft_version": "1.99.0"}):
            assert vc.get_minecraft_version() == "1.99.0"


# ===========================================================================
# load_version_profile
# ===========================================================================

class TestLoadVersionProfile:
    def test_loads_real_1_20_4_profile(self):
        profile = vc.load_version_profile("1.20.4")
        assert profile["minecraft_version"] == "1.20.4"
        assert profile["pack_format"] == 41
        assert "templates" in profile
        assert "paths" in profile

    def test_profile_has_required_keys(self):
        profile = vc.load_version_profile("1.20.4")
        assert "paths" in profile
        assert "function_dir" in profile["paths"]
        assert "function_tag_dir" in profile["paths"]
        assert "constants" in profile
        assert "templates" in profile

    def test_caches_profile_after_first_load(self):
        vc._profile_cache.clear()
        profile1 = vc.load_version_profile("1.20.4")
        profile2 = vc.load_version_profile("1.20.4")
        assert profile1 is profile2  # same object from cache

    def test_uses_common_config_version_when_none_given(self):
        vc._profile_cache.clear()
        with patch.object(vc, "COMMON_CONFIG", {"minecraft_version": "1.20.4"}):
            profile = vc.load_version_profile(None)
        assert profile["minecraft_version"] == "1.20.4"

    def test_raises_file_not_found_for_unknown_version(self):
        with pytest.raises(FileNotFoundError) as exc_info:
            vc.load_version_profile("9.99.99")
        assert "9.99.99" in str(exc_info.value)
        assert "Unknown minecraft version" in str(exc_info.value)

    def test_error_message_includes_supported_versions(self):
        with pytest.raises(FileNotFoundError) as exc_info:
            vc.load_version_profile("9.99.99")
        error_text = str(exc_info.value)
        # Should mention supported versions or 'none'
        assert "Supported:" in error_text

    def test_uses_cached_profile_without_reading_file(self):
        vc._profile_cache["fake_version"] = MINIMAL_PROFILE
        profile = vc.load_version_profile("fake_version")
        assert profile is MINIMAL_PROFILE


# ===========================================================================
# list_supported_versions
# ===========================================================================

class TestListSupportedVersions:
    def test_returns_list(self):
        versions = vc.list_supported_versions()
        assert isinstance(versions, list)

    def test_includes_1_20_4(self):
        versions = vc.list_supported_versions()
        assert "1.20.4" in versions

    def test_excludes_index_json(self):
        versions = vc.list_supported_versions()
        assert "index" not in versions

    def test_returns_sorted_list(self):
        versions = vc.list_supported_versions()
        assert versions == sorted(versions)

    def test_returns_empty_when_versions_dir_missing(self, tmp_path):
        nonexistent = tmp_path / "no_such_dir"
        with patch.object(vc, "module_folder", str(tmp_path / "fake_module")):
            result = vc.list_supported_versions()
        assert result == []

    def test_returns_only_json_stems(self):
        versions = vc.list_supported_versions()
        for v in versions:
            assert "." in v or v.isidentifier()  # version strings should be reasonable


# ===========================================================================
# predefined_root
# ===========================================================================

class TestPredefinedRoot:
    def test_returns_string(self):
        result = vc.predefined_root("math", "1.20.4")
        assert isinstance(result, str)

    def test_path_contains_version(self):
        result = vc.predefined_root("math", "1.20.4")
        assert "1.20.4" in result

    def test_path_contains_category(self):
        result = vc.predefined_root("math", "1.20.4")
        assert "math" in result

    def test_path_ends_with_version_and_category(self):
        result = vc.predefined_root("builtins", "1.20.4")
        assert result.endswith("builtins/1.20.4")

    def test_uses_current_version_when_none(self):
        with patch.object(vc, "COMMON_CONFIG", {"minecraft_version": "1.20.4"}):
            result = vc.predefined_root("tags")
        assert "1.20.4" in result
        assert "tags" in result

    def test_explicit_version_overrides_config(self):
        with patch.object(vc, "COMMON_CONFIG", {"minecraft_version": "1.20.4"}):
            result = vc.predefined_root("math", "2.0.0")
        assert "2.0.0" in result
        assert "1.20.4" not in result

    def test_math_path_exists_for_1_20_4(self):
        result = vc.predefined_root("math", "1.20.4")
        assert Path(result).is_dir()

    def test_builtins_path_exists_for_1_20_4(self):
        result = vc.predefined_root("builtins", "1.20.4")
        assert Path(result).is_dir()

    def test_tags_path_exists_for_1_20_4(self):
        result = vc.predefined_root("tags", "1.20.4")
        assert Path(result).is_dir()


# ===========================================================================
# VersionRenderer
# ===========================================================================

class TestVersionRenderer:
    def setup_method(self):
        self.renderer = vc.VersionRenderer(MINIMAL_PROFILE)

    def test_render_simple_template(self):
        result = self.renderer.render("simple", name="world")
        assert result == "hello world"

    def test_render_no_params_template(self):
        result = self.renderer.render("no_params")
        assert result == "static text"

    def test_render_strips_whitespace(self):
        profile = {**MINIMAL_PROFILE, "templates": {"padded": "  hello  "}}
        renderer = vc.VersionRenderer(profile)
        assert renderer.render("padded") == "hello"

    def test_render_raises_key_error_for_missing_key(self):
        with pytest.raises(KeyError) as exc_info:
            self.renderer.render("nonexistent_key")
        assert "nonexistent_key" in str(exc_info.value)

    def test_render_raises_key_error_when_no_templates_key(self):
        renderer = vc.VersionRenderer({"minecraft_version": "0.0"})
        with pytest.raises(KeyError):
            renderer.render("anything")

    def test_render_compiles_template_once_and_caches(self):
        self.renderer.render("simple", name="first")
        compiled_before = dict(self.renderer._compiled)
        self.renderer.render("simple", name="second")
        assert set(self.renderer._compiled.keys()) == set(compiled_before.keys())

    def test_render_lines_splits_on_newlines(self):
        result = self.renderer.render_lines("multiline", value="test")
        assert result == ["line1", "line2 test", "line3"]

    def test_render_lines_single_line(self):
        result = self.renderer.render_lines("simple", name="x")
        assert result == ["hello x"]

    def test_render_lines_returns_empty_list_for_empty_output(self):
        profile = {**MINIMAL_PROFILE, "templates": {"empty": ""}}
        renderer = vc.VersionRenderer(profile)
        result = renderer.render_lines("empty")
        assert result == []

    def test_render_conditional_true(self):
        result = self.renderer.render("conditional", flag=True)
        assert result == "yes"

    def test_render_conditional_false(self):
        result = self.renderer.render("conditional", flag=False)
        assert result == "no"


# ===========================================================================
# VersionContext
# ===========================================================================

class TestVersionContext:
    def test_init_with_explicit_profile(self):
        ctx = vc.VersionContext("my_pack", profile=MINIMAL_PROFILE)
        assert ctx.datapack_id == "my_pack"
        assert ctx.profile is MINIMAL_PROFILE

    def test_init_reads_function_dir_from_profile(self):
        ctx = vc.VersionContext("my_pack", profile=MINIMAL_PROFILE)
        assert ctx.function_dir == "functions"

    def test_init_reads_function_tag_dir_from_profile(self):
        ctx = vc.VersionContext("my_pack", profile=MINIMAL_PROFILE)
        assert ctx.function_tag_dir == "functions"

    def test_init_sets_pack_format_as_string(self):
        ctx = vc.VersionContext("my_pack", profile=MINIMAL_PROFILE)
        assert ctx.pack_format == "99"
        assert isinstance(ctx.pack_format, str)

    def test_init_loads_real_profile_when_none_given(self):
        vc._profile_cache.clear()
        with patch.object(vc, "COMMON_CONFIG", {"minecraft_version": "1.20.4"}):
            ctx = vc.VersionContext("dp")
        assert ctx.profile["minecraft_version"] == "1.20.4"

    def test_params_merges_constants(self):
        ctx = vc.VersionContext("my_pack", profile=MINIMAL_PROFILE)
        params = ctx._params(extra="val")
        assert params["testConst"] == "hello"
        assert params["extra"] == "val"

    def test_params_adds_datapack_id(self):
        ctx = vc.VersionContext("my_pack", profile=MINIMAL_PROFILE)
        params = ctx._params()
        assert params["datapack_id"] == "my_pack"

    def test_params_caller_overrides_datapack_id(self):
        ctx = vc.VersionContext("my_pack", profile=MINIMAL_PROFILE)
        params = ctx._params(datapack_id="override")
        assert params["datapack_id"] == "override"

    def test_params_caller_overrides_constant(self):
        ctx = vc.VersionContext("my_pack", profile=MINIMAL_PROFILE)
        params = ctx._params(testConst="overridden")
        assert params["testConst"] == "overridden"

    def test_render_injects_datapack_id(self):
        ctx = vc.VersionContext("my_pack", profile=MINIMAL_PROFILE)
        result = ctx.render("datapack_ref")
        assert result == "function my_pack:something"

    def test_render_injects_constants(self):
        ctx = vc.VersionContext("my_pack", profile=MINIMAL_PROFILE)
        result = ctx.render("with_const")
        assert result == "hello world"

    def test_render_passes_caller_params(self):
        ctx = vc.VersionContext("my_pack", profile=MINIMAL_PROFILE)
        result = ctx.render("simple", name="earth")
        assert result == "hello earth"

    def test_render_lines_returns_list(self):
        ctx = vc.VersionContext("my_pack", profile=MINIMAL_PROFILE)
        result = ctx.render_lines("multiline", value="x")
        assert isinstance(result, list)
        assert len(result) == 3

    def test_render_lines_splits_correctly(self):
        ctx = vc.VersionContext("my_pack", profile=MINIMAL_PROFILE)
        result = ctx.render_lines("multiline", value="abc")
        assert result[1] == "line2 abc"

    def test_render_raises_key_error_for_missing_template(self):
        ctx = vc.VersionContext("my_pack", profile=MINIMAL_PROFILE)
        with pytest.raises(KeyError) as exc_info:
            ctx.render("nonexistent")
        assert "nonexistent" in str(exc_info.value)


# ===========================================================================
# 1.20.4 profile templates (smoke tests for actual content)
# ===========================================================================

class TestRealProfile1204Templates:
    """Smoke tests verifying key templates in the 1.20.4 profile render correctly."""

    def setup_method(self):
        vc._profile_cache.clear()
        self.ctx = vc.VersionContext("my_dp", profile=vc.load_version_profile("1.20.4"))

    def test_datapack_init_contains_scoreboard(self):
        result = self.ctx.render("datapack.init")
        assert "scoreboard objectives add mcs_math" in result

    def test_datapack_init_references_datapack_id(self):
        result = self.ctx.render("datapack.init")
        assert "my_dp" in result

    def test_datapack_kill_contains_datapack_name(self):
        result = self.ctx.render("datapack.kill", datapackName="test_dp_name")
        assert "test_dp_name" in result

    def test_datapack_main_references_datapack_id(self):
        result = self.ctx.render("datapack.main")
        assert "my_dp" in result

    def test_literal_save_template(self):
        result = self.ctx.render("literal.save", storage="my_storage", nbt="my.nbt", value=42)
        assert "data modify storage my_storage my.nbt set value 42" in result

    def test_literal_delete_template(self):
        result = self.ctx.render("literal.delete", storage="my_storage", nbt="my.nbt")
        assert "data remove storage my_storage my.nbt" in result

    def test_literal_set_to_current_template(self):
        result = self.ctx.render(
            "literal.set_to_current",
            destStorage="dest_store",
            storage="src_store",
            nbt="my.nbt",
        )
        assert "data modify storage dest_store current set from storage src_store my.nbt" in result

    def test_variable_declare_template(self):
        result = self.ctx.render(
            "variable.declare",
            ownerStorage="mcs_abc",
            name="myVar",
            valueStorage="mcs_xyz",
            valueNbt="number.123",
        )
        assert "data modify storage mcs_abc variable.myVar set from storage mcs_xyz number.123" in result

    def test_math_binary_template(self):
        result = self.ctx.render(
            "math.binary",
            leftStorage="mcs_l",
            leftNbt="number.1",
            rightStorage="mcs_r",
            rightNbt="number.2",
            operation="add",
            resultStorage="mcs_res",
            resultNbt="number.out",
        )
        lines = result.split("\n")
        assert any("score .a mcs_math" in l for l in lines)
        assert any("score .b mcs_math" in l for l in lines)
        assert any("math/add" in l for l in lines)

    def test_math_unary_template(self):
        result = self.ctx.render(
            "math.unary",
            rootStorage="mcs_r",
            rootNbt="number.1",
            operation="u_not",
            resultStorage="mcs_res",
            resultNbt="boolean.out",
        )
        assert "math/u_not" in result

    def test_control_if_branch_template(self):
        result = self.ctx.render(
            "control.if.branch",
            exprStorage="mcs_e",
            exprNbt="boolean.1",
            branchStorage="mcs_b",
            parentStorage="mcs_p",
            branchPath="code_blocks/foo",
        )
        assert ".out mcs_math" in result
        assert "return 0" in result

    def test_control_for_init_template(self):
        result = self.ctx.render(
            "control.for.init",
            loopId="loop123",
            iterableStorage="mcs_i",
            iterableNbt="list.1",
            loopPath="code_blocks/loop",
        )
        assert "loop_iter_loop123" in result
        assert "loop_end_loop123" in result

    def test_kill_remove_compartment_template(self):
        result = self.ctx.render(
            "kill.remove_compartment",
            ctxStorage="mcs_abc123",
            compartment="number",
        )
        assert "data remove storage mcs_abc123 number" in result

    def test_function_call_invoke_template(self):
        result = self.ctx.render("function.call.invoke", functionName="my_func")
        assert "my_dp:user_functions/my_func" in result

    def test_click_check_template(self):
        result = self.ctx.render("click.check")
        assert "mcs_click" in result
        assert "my_dp" in result

    def test_builtin_log_template(self):
        result = self.ctx.render("builtin.log", storageSuffix=" {s0: foo}")
        assert "builtins/log" in result
        assert "my_dp" in result

    def test_builtin_give_item_setup_with_components(self):
        result = self.ctx.render(
            "builtin.give_item.setup",
            ctxStorage="mcs_ctx",
            itemStorage="mcs_item",
            itemNbt="string.1",
            hasComponents=True,
            componentsStorage="mcs_comp",
            componentsNbt="string.2",
            hasCount=False,
        )
        assert "current.item" in result
        assert "current.components set from" in result
        assert "builtins/give_item" in result

    def test_builtin_give_item_setup_without_components(self):
        result = self.ctx.render(
            "builtin.give_item.setup",
            ctxStorage="mcs_ctx",
            itemStorage="mcs_item",
            itemNbt="string.1",
            hasComponents=False,
            hasCount=False,
        )
        assert "current.components set value ''" in result

    def test_builtin_give_item_setup_with_count(self):
        result = self.ctx.render(
            "builtin.give_item.setup",
            ctxStorage="mcs_ctx",
            itemStorage="mcs_item",
            itemNbt="string.1",
            hasComponents=False,
            hasCount=True,
            countStorage="mcs_count",
            countNbt="number.3",
        )
        assert "current.count set from" in result

    def test_builtin_give_item_setup_default_count(self):
        result = self.ctx.render(
            "builtin.give_item.setup",
            ctxStorage="mcs_ctx",
            itemStorage="mcs_item",
            itemNbt="string.1",
            hasComponents=False,
            hasCount=False,
        )
        assert "current.count set value 1" in result

    def test_pack_mcmeta_contains_pack_format(self):
        result = self.ctx.render("pack.mcmeta", pack_format=41)
        assert "41" in result
        assert "pack_format" in result

    def test_builtin_raycast_block_loop_has_no_loop_function(self):
        result = self.ctx.render(
            "builtin.raycast_block.loop",
            raycastId="abc",
            hitFunction="my_hit",
            hasLoopFunction=False,
            loopFunction="",
            loopPath="code_blocks/rc",
        )
        assert "# No loop function" in result

    def test_builtin_raycast_block_loop_with_loop_function(self):
        result = self.ctx.render(
            "builtin.raycast_block.loop",
            raycastId="abc",
            hitFunction="my_hit",
            hasLoopFunction=True,
            loopFunction="my_loop",
            loopPath="code_blocks/rc",
        )
        assert "user_functions/my_loop" in result
        assert "# No loop function" not in result


# ===========================================================================
# init_version_context / get_version_context / clear_version_context
# ===========================================================================

class TestVersionContextLifecycle:
    def test_init_version_context_returns_context(self):
        ctx = vc.init_version_context("test_pack")
        assert isinstance(ctx, vc.VersionContext)

    def test_init_version_context_sets_datapack_id(self):
        ctx = vc.init_version_context("my_dp_id")
        assert ctx.datapack_id == "my_dp_id"

    def test_get_version_context_returns_same_object(self):
        ctx = vc.init_version_context("dp")
        got = vc.get_version_context()
        assert got is ctx

    def test_get_version_context_raises_when_not_initialized(self):
        vc.clear_version_context()
        with pytest.raises(RuntimeError) as exc_info:
            vc.get_version_context()
        assert "not initialized" in str(exc_info.value).lower()

    def test_clear_version_context_causes_get_to_raise(self):
        vc.init_version_context("dp")
        vc.clear_version_context()
        with pytest.raises(RuntimeError):
            vc.get_version_context()

    def test_init_replaces_existing_context(self):
        ctx1 = vc.init_version_context("dp1")
        ctx2 = vc.init_version_context("dp2")
        assert vc.get_version_context() is ctx2
        assert ctx1 is not ctx2

    def test_clear_allows_re_init(self):
        vc.init_version_context("dp")
        vc.clear_version_context()
        ctx = vc.init_version_context("dp2")
        assert vc.get_version_context() is ctx

    def test_get_raises_with_helpful_message(self):
        vc.clear_version_context()
        with pytest.raises(RuntimeError) as exc_info:
            vc.get_version_context()
        assert "init_version_context" in str(exc_info.value)
