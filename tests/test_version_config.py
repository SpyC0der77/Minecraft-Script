"""
Tests for minecraft_script/version_config.py

Covers: VersionRenderer, VersionContext, load_version_profile,
list_supported_versions, predefined_root, init/get/clear_version_context.
"""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch

import minecraft_script.version_config as vc
from minecraft_script.version_config import (
    VersionRenderer,
    VersionContext,
    load_version_profile,
    list_supported_versions,
    predefined_root,
    init_version_context,
    get_version_context,
    clear_version_context,
    get_minecraft_version,
)


# ---------------------------------------------------------------------------
# get_minecraft_version
# ---------------------------------------------------------------------------

class TestGetMinecraftVersion:
    def test_returns_configured_version(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        assert get_minecraft_version() == "1.20.4"

    def test_reflects_config_change(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "9.9.9"
        assert get_minecraft_version() == "9.9.9"
        COMMON_CONFIG["minecraft_version"] = "1.20.4"  # restore


# ---------------------------------------------------------------------------
# load_version_profile
# ---------------------------------------------------------------------------

class TestLoadVersionProfile:
    def test_loads_known_version(self):
        profile = load_version_profile("1.20.4")
        assert profile["minecraft_version"] == "1.20.4"
        assert profile["pack_format"] == 41

    def test_profile_has_required_keys(self):
        profile = load_version_profile("1.20.4")
        assert "paths" in profile
        assert "templates" in profile
        assert "constants" in profile

    def test_unknown_version_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="Unknown minecraft version"):
            load_version_profile("0.0.0")

    def test_unknown_version_error_mentions_supported(self):
        with pytest.raises(FileNotFoundError, match="1.20.4"):
            load_version_profile("0.0.0")

    def test_caching_returns_same_object(self):
        p1 = load_version_profile("1.20.4")
        p2 = load_version_profile("1.20.4")
        assert p1 is p2

    def test_uses_common_config_version_when_none_given(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        profile = load_version_profile()
        assert profile["minecraft_version"] == "1.20.4"

    def test_cache_cleared_between_tests(self):
        # conftest clears cache; this profile load should succeed fresh
        profile = load_version_profile("1.20.4")
        assert profile is not None


# ---------------------------------------------------------------------------
# list_supported_versions
# ---------------------------------------------------------------------------

class TestListSupportedVersions:
    def test_contains_1204(self):
        versions = list_supported_versions()
        assert "1.20.4" in versions

    def test_excludes_index_json(self):
        versions = list_supported_versions()
        assert "index" not in versions

    def test_returns_sorted_list(self):
        versions = list_supported_versions()
        assert versions == sorted(versions)

    def test_returns_list(self):
        versions = list_supported_versions()
        assert isinstance(versions, list)

    def test_nonexistent_versions_dir_returns_empty(self):
        with patch.object(Path, "is_dir", return_value=False):
            result = list_supported_versions()
        assert result == []


# ---------------------------------------------------------------------------
# predefined_root
# ---------------------------------------------------------------------------

class TestPredefinedRoot:
    def test_math_root_for_1204(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        path = predefined_root("math")
        assert path.endswith(os.path.join("math", "1.20.4"))

    def test_explicit_version_override(self):
        path = predefined_root("math", version="9.9.9")
        assert path.endswith(os.path.join("math", "9.9.9"))

    def test_builtins_category(self):
        path = predefined_root("builtins", version="1.20.4")
        assert "builtins" in path
        assert "1.20.4" in path

    def test_tags_category(self):
        path = predefined_root("tags", version="1.20.4")
        assert "tags" in path

    def test_path_is_string(self):
        path = predefined_root("math", version="1.20.4")
        assert isinstance(path, str)


# ---------------------------------------------------------------------------
# VersionRenderer
# ---------------------------------------------------------------------------

class TestVersionRenderer:
    def test_render_simple_template(self, mock_profile):
        renderer = VersionRenderer(mock_profile)
        result = renderer.render("simple")
        assert result == "just text"

    def test_render_with_variable(self, mock_profile):
        renderer = VersionRenderer(mock_profile)
        result = renderer.render("with_var", myVar="world")
        assert result == "value=world"

    def test_render_missing_key_raises(self, mock_profile):
        renderer = VersionRenderer(mock_profile)
        with pytest.raises(KeyError, match="Template 'nonexistent' not defined"):
            renderer.render("nonexistent")

    def test_render_strips_surrounding_whitespace(self, mock_profile):
        mock_profile["templates"]["padded"] = "  hello  "
        renderer = VersionRenderer(mock_profile)
        result = renderer.render("padded")
        assert result == "hello"

    def test_render_lines_splits_on_newline(self, mock_profile):
        renderer = VersionRenderer(mock_profile)
        lines = renderer.render_lines("multiline")
        assert lines == ["line1", "line2", "line3"]

    def test_render_lines_empty_template_returns_empty_list(self, mock_profile):
        renderer = VersionRenderer(mock_profile)
        lines = renderer.render_lines("empty")
        assert lines == []

    def test_compiled_template_is_cached(self, mock_profile):
        renderer = VersionRenderer(mock_profile)
        renderer.render("simple")
        assert "simple" in renderer._compiled
        # Second call still works
        assert renderer.render("simple") == "just text"

    def test_conditional_true_branch(self, mock_profile):
        renderer = VersionRenderer(mock_profile)
        result = renderer.render("conditional", flag=True)
        assert result == "yes"

    def test_conditional_false_branch(self, mock_profile):
        renderer = VersionRenderer(mock_profile)
        result = renderer.render("conditional", flag=False)
        assert result == "no"

    def test_missing_templates_key_raises(self):
        profile_no_templates = {"minecraft_version": "x", "pack_format": 0}
        renderer = VersionRenderer(profile_no_templates)
        with pytest.raises(KeyError):
            renderer.render("anything")


# ---------------------------------------------------------------------------
# VersionContext
# ---------------------------------------------------------------------------

class TestVersionContext:
    def test_init_sets_datapack_id(self, profile_1204):
        ctx = VersionContext("my_pack", profile=profile_1204)
        assert ctx.datapack_id == "my_pack"

    def test_init_sets_function_dir(self, profile_1204):
        ctx = VersionContext("dp", profile=profile_1204)
        assert ctx.function_dir == "functions"

    def test_init_sets_function_tag_dir(self, profile_1204):
        ctx = VersionContext("dp", profile=profile_1204)
        assert ctx.function_tag_dir == "functions"

    def test_init_sets_pack_format_as_string(self, profile_1204):
        ctx = VersionContext("dp", profile=profile_1204)
        assert ctx.pack_format == "41"

    def test_render_uses_datapack_id_constant(self, profile_1204):
        ctx = VersionContext("mypack", profile=profile_1204)
        result = ctx.render("function.call.invoke", functionName="foo")
        assert "mypack" in result
        assert "foo" in result

    def test_render_injects_version_constants(self, profile_1204):
        ctx = VersionContext("dp", profile=profile_1204)
        # click.check uses clickSelectedItemPath constant from profile
        result = ctx.render("click.check")
        assert "SelectedItem.tag.mcs_click" in result

    def test_params_merges_constants_with_extra(self, profile_1204):
        ctx = VersionContext("dp", profile=profile_1204)
        params = ctx._params(extra="value")
        assert params["extra"] == "value"
        assert params["datapack_id"] == "dp"
        assert "clickScoreboardCriterion" in params

    def test_params_extra_overrides_constants(self, profile_1204):
        ctx = VersionContext("dp", profile=profile_1204)
        params = ctx._params(datapack_id="override")
        assert params["datapack_id"] == "override"

    def test_render_lines_returns_list(self, profile_1204):
        ctx = VersionContext("dp", profile=profile_1204)
        lines = ctx.render_lines("control.while.tail", condStorage="s", condNbt="n", loopPath="lp")
        assert isinstance(lines, list)
        assert len(lines) > 0

    def test_render_lines_pack_format_placeholder(self, profile_1204):
        ctx = VersionContext("dp", profile=profile_1204)
        # pack_format must be passed explicitly (same as compiler.py does)
        result = ctx.render("pack.mcmeta", pack_format=ctx.pack_format)
        assert "41" in result

    def test_render_datapack_kill_includes_datapack_name(self, profile_1204):
        ctx = VersionContext("dp", profile=profile_1204)
        result = ctx.render("datapack.kill", datapackName="my_datapack")
        assert "my_datapack" in result

    def test_loads_profile_automatically_without_explicit_profile(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        ctx = VersionContext("auto_pack")
        assert ctx.profile["minecraft_version"] == "1.20.4"


# ---------------------------------------------------------------------------
# Global context management: init / get / clear
# ---------------------------------------------------------------------------

class TestVersionContextGlobals:
    def test_get_before_init_raises_runtime_error(self):
        with pytest.raises(RuntimeError, match="Version context not initialized"):
            get_version_context()

    def test_init_returns_context(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        ctx = init_version_context("pack")
        assert isinstance(ctx, VersionContext)

    def test_get_after_init_returns_same_context(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        ctx = init_version_context("pack")
        assert get_version_context() is ctx

    def test_clear_resets_context(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        init_version_context("pack")
        clear_version_context()
        with pytest.raises(RuntimeError):
            get_version_context()

    def test_init_overwrites_previous_context(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        ctx1 = init_version_context("pack1")
        ctx2 = init_version_context("pack2")
        assert get_version_context() is ctx2
        assert ctx1 is not ctx2

    def test_context_datapack_id_matches_init_arg(self):
        from minecraft_script.common import COMMON_CONFIG
        COMMON_CONFIG["minecraft_version"] = "1.20.4"
        ctx = init_version_context("custom_id")
        assert ctx.datapack_id == "custom_id"


# ---------------------------------------------------------------------------
# Template rendering - 1.20.4 specific spot checks
# ---------------------------------------------------------------------------

class TestTemplateRendering1204:
    """Integration tests ensuring specific 1.20.4 templates render correctly."""

    def test_literal_save(self, version_ctx_1204):
        result = version_ctx_1204.render("literal.save", storage="mcs_abc", nbt="number.xyz", value=42)
        assert result == "data modify storage mcs_abc number.xyz set value 42"

    def test_literal_delete(self, version_ctx_1204):
        result = version_ctx_1204.render("literal.delete", storage="mcs_abc", nbt="number.xyz")
        assert result == "data remove storage mcs_abc number.xyz"

    def test_literal_set_to_current(self, version_ctx_1204):
        result = version_ctx_1204.render(
            "literal.set_to_current", destStorage="mcs_dest", storage="mcs_src", nbt="number.n"
        )
        assert "data modify storage mcs_dest current set from storage mcs_src number.n" == result

    def test_variable_declare(self, version_ctx_1204):
        result = version_ctx_1204.render(
            "variable.declare",
            ownerStorage="mcs_owner", name="x", valueStorage="mcs_val", valueNbt="number.n"
        )
        assert "variable.x" in result
        assert "mcs_owner" in result

    def test_variable_assign(self, version_ctx_1204):
        result = version_ctx_1204.render(
            "variable.assign",
            ownerStorage="mcs_owner", name="myVar", valueStorage="mcs_src", valueNbt="string.s"
        )
        assert "variable.myVar" in result

    def test_kill_remove_compartment(self, version_ctx_1204):
        result = version_ctx_1204.render(
            "kill.remove_compartment", ctxStorage="mcs_abc", compartment="number"
        )
        assert result == "data remove storage mcs_abc number"

    def test_function_call_invoke(self, version_ctx_1204):
        result = version_ctx_1204.render("function.call.invoke", functionName="my_func")
        assert result == "function test_pack:user_functions/my_func"

    def test_function_call_param(self, version_ctx_1204):
        lines = version_ctx_1204.render_lines(
            "function.call.param",
            localStorage="mcs_local", argStorage="mcs_arg", argNbt="string.s", paramName="foo"
        )
        assert len(lines) == 2
        assert "mcs_local" in lines[0]
        assert "variable.foo" in lines[1]

    def test_math_binary_renders(self, version_ctx_1204):
        lines = version_ctx_1204.render_lines(
            "math.binary",
            leftStorage="mcs_a", leftNbt="number.x",
            rightStorage="mcs_b", rightNbt="number.y",
            operation="add",
            resultStorage="mcs_r", resultNbt="number.z",
        )
        assert any(".a" in l for l in lines)
        assert any(".b" in l for l in lines)
        assert any("math/add" in l for l in lines)

    def test_math_unary_renders(self, version_ctx_1204):
        lines = version_ctx_1204.render_lines(
            "math.unary",
            rootStorage="mcs_r", rootNbt="boolean.b",
            operation="u_not",
            resultStorage="mcs_out", resultNbt="boolean.b2",
        )
        assert any("math/u_not" in l for l in lines)

    def test_control_if_branch_renders(self, version_ctx_1204):
        lines = version_ctx_1204.render_lines(
            "control.if.branch",
            exprStorage="mcs_e", exprNbt="boolean.b",
            branchStorage="mcs_br", parentStorage="mcs_p",
            branchPath="code_blocks/cb_abc",
        )
        assert any("score" in l for l in lines)
        assert any("return 0" in l for l in lines)

    def test_control_for_init_renders(self, version_ctx_1204):
        lines = version_ctx_1204.render_lines(
            "control.for.init",
            loopId="abc123",
            iterableStorage="mcs_it", iterableNbt="list.l",
            loopPath="code_blocks/loop",
        )
        assert any("loop_iter_abc123" in l for l in lines)
        assert any("loop_end_abc123" in l for l in lines)

    def test_click_check_uses_correct_path(self, version_ctx_1204):
        result = version_ctx_1204.render("click.check")
        assert "SelectedItem.tag.mcs_click" in result
        assert "test_pack:clickable_items/run" in result

    def test_click_run_renders(self, version_ctx_1204):
        result = version_ctx_1204.render("click.run")
        assert "test_pack:clickable_items/$(id)" in result

    def test_datapack_init_uses_carrot_on_a_stick(self, version_ctx_1204):
        result = version_ctx_1204.render("datapack.init")
        assert "minecraft.used:minecraft.carrot_on_a_stick" in result

    def test_builtin_log_renders(self, version_ctx_1204):
        suffix = ' {"s0": "mcs_abc", "n0": "number.x"}'
        result = version_ctx_1204.render("builtin.log", storageSuffix=suffix)
        assert "test_pack:builtins/log" in result
        assert suffix in result

    def test_builtin_give_item_with_components(self, version_ctx_1204):
        lines = version_ctx_1204.render_lines(
            "builtin.give_item.setup",
            ctxStorage="mcs_c",
            itemStorage="mcs_i", itemNbt="string.s",
            hasComponents=True,
            componentsStorage="mcs_comp", componentsNbt="string.c",
            hasCount=False,
        )
        full = "\n".join(lines)
        assert "current.components set from storage mcs_comp" in full
        assert "current.count set value 1" in full

    def test_builtin_give_item_without_components(self, version_ctx_1204):
        lines = version_ctx_1204.render_lines(
            "builtin.give_item.setup",
            ctxStorage="mcs_c",
            itemStorage="mcs_i", itemNbt="string.s",
            hasComponents=False,
            hasCount=False,
        )
        full = "\n".join(lines)
        assert "current.components set value ''" in full

    def test_pack_mcmeta_has_pack_format(self, version_ctx_1204):
        result = version_ctx_1204.render("pack.mcmeta", pack_format=version_ctx_1204.pack_format)
        assert '"pack_format": 41' in result

    def test_index_setup_renders(self, version_ctx_1204):
        lines = version_ctx_1204.render_lines(
            "index.setup",
            ctxStorage="mcs_ctx",
            keyStorage="mcs_key", keyNbt="number.n",
            macroPath="code_blocks/macro",
        )
        full = "\n".join(lines)
        assert "current.index" in full
        assert "code_blocks/macro" in full

    def test_literal_list_length(self, version_ctx_1204):
        result = version_ctx_1204.render(
            "literal.list.length", storage="mcs_abc", nbt="list.l", length=5
        )
        assert ".length set value 5" in result

    def test_literal_list_element(self, version_ctx_1204):
        result = version_ctx_1204.render(
            "literal.list.element", storage="mcs_abc", nbt="list.l", index=2, srcStorage="mcs_src"
        )
        assert "list.l.2" in result
        assert "current" in result

    def test_builtin_give_clickable_simple(self, version_ctx_1204):
        result = version_ctx_1204.render("builtin.give_clickable.simple", clickId=3)
        assert "carrot_on_a_stick" in result
        assert "mcs_click:3" in result

    def test_raycast_block_loop_with_loop_function(self, version_ctx_1204):
        lines = version_ctx_1204.render_lines(
            "builtin.raycast_block.loop",
            raycastId="ray123",
            hitFunction="my_hit",
            hasLoopFunction=True,
            loopFunction="my_loop",
            loopPath="code_blocks/loop",
        )
        full = "\n".join(lines)
        assert "user_functions/my_hit" in full
        assert "user_functions/my_loop" in full

    def test_raycast_block_loop_without_loop_function(self, version_ctx_1204):
        lines = version_ctx_1204.render_lines(
            "builtin.raycast_block.loop",
            raycastId="ray123",
            hitFunction="my_hit",
            hasLoopFunction=False,
            loopFunction="",
            loopPath="code_blocks/loop",
        )
        full = "\n".join(lines)
        assert "# No loop function" in full
        assert "user_functions/my_hit" in full
