"""
Tests for minecraft_script/compiler/builtin_functions.py

Covers the version-context-based rendering for: log, command, give_item,
set_block, concatenate, append - focusing on command generation correctness
introduced in this PR.
"""
import pytest
from unittest.mock import MagicMock, patch

from minecraft_script.version_config import init_version_context
from minecraft_script.compiler.compile_types import (
    MCSNull, MCSNumber, MCSString, MCSList, MCSFunction, MCSBoolean
)
from minecraft_script.compiler.builtin_functions import (
    log, command, give_item, set_block, concatenate, append
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ctx(version_ctx_1204):
    from minecraft_script.compiler.compile_interpreter import CompileContext
    return CompileContext("test_fn", top_level=True)


@pytest.fixture
def mock_interp(ctx):
    interp = MagicMock()
    interp.datapack_id = "test_pack"
    interp.click_item_lookup = {}
    return interp


# ---------------------------------------------------------------------------
# log()
# ---------------------------------------------------------------------------

class TestLog:
    def test_returns_null(self, mock_interp, ctx):
        arg = MCSNumber(ctx)
        cmds, ret = log(mock_interp, [arg], ctx)
        assert isinstance(ret, MCSNull)

    def test_single_arg_produces_one_command(self, mock_interp, ctx):
        arg = MCSNumber(ctx)
        cmds, _ = log(mock_interp, [arg], ctx)
        assert len(cmds) == 1

    def test_command_calls_builtins_log(self, mock_interp, ctx):
        arg = MCSNumber(ctx)
        cmds, _ = log(mock_interp, [arg], ctx)
        assert "builtins/log" in cmds[0]

    def test_storage_suffix_contains_arg_storage(self, mock_interp, ctx):
        arg = MCSNumber(ctx)
        cmds, _ = log(mock_interp, [arg], ctx)
        assert arg.get_storage() in cmds[0]

    def test_storage_suffix_contains_arg_nbt(self, mock_interp, ctx):
        arg = MCSNumber(ctx)
        cmds, _ = log(mock_interp, [arg], ctx)
        assert arg.get_nbt() in cmds[0]

    def test_no_args_pads_to_five_empty(self, mock_interp, ctx):
        cmds, _ = log(mock_interp, [], ctx)
        # All 5 slots should have empty storage/nbt
        assert '"s0": ""' in cmds[0]
        assert '"n4": "none"' in cmds[0]

    def test_five_args_no_padding(self, mock_interp, ctx):
        args = [MCSNumber(ctx) for _ in range(5)]
        cmds, _ = log(mock_interp, args, ctx)
        assert '"n4"' in cmds[0]
        assert '"n5"' not in cmds[0]

    def test_datapack_id_in_command(self, mock_interp, ctx):
        arg = MCSString(ctx)
        cmds, _ = log(mock_interp, [arg], ctx)
        assert "test_pack" in cmds[0]


# ---------------------------------------------------------------------------
# command()
# ---------------------------------------------------------------------------

class TestCommand:
    def test_returns_null(self, mock_interp, ctx):
        arg = MCSString(ctx)
        cmds, ret = command(mock_interp, [arg], ctx)
        assert isinstance(ret, MCSNull)

    def test_command_references_value_storage(self, mock_interp, ctx):
        arg = MCSString(ctx)
        cmds, _ = command(mock_interp, [arg], ctx)
        full = "\n".join(cmds)
        assert arg.get_storage() in full

    def test_command_calls_builtins_command(self, mock_interp, ctx):
        arg = MCSString(ctx)
        cmds, _ = command(mock_interp, [arg], ctx)
        full = "\n".join(cmds)
        assert "builtins/command" in full

    def test_command_uses_with_storage(self, mock_interp, ctx):
        arg = MCSString(ctx)
        cmds, _ = command(mock_interp, [arg], ctx)
        full = "\n".join(cmds)
        assert "with storage" in full

    def test_command_produces_multiple_lines(self, mock_interp, ctx):
        arg = MCSString(ctx)
        cmds, _ = command(mock_interp, [arg], ctx)
        assert len(cmds) >= 2


# ---------------------------------------------------------------------------
# give_item()
# ---------------------------------------------------------------------------

class TestGiveItem:
    def test_returns_null(self, mock_interp, ctx):
        item = MCSString(ctx)
        cmds, ret = give_item(mock_interp, [item], ctx)
        assert isinstance(ret, MCSNull)

    def test_item_only_uses_default_components_and_count(self, mock_interp, ctx):
        item = MCSString(ctx)
        cmds, _ = give_item(mock_interp, [item], ctx)
        full = "\n".join(cmds)
        assert "current.components set value ''" in full
        assert "current.count set value 1" in full

    def test_with_components_uses_storage(self, mock_interp, ctx):
        item = MCSString(ctx)
        comps = MCSString(ctx)
        cmds, _ = give_item(mock_interp, [item, comps], ctx)
        full = "\n".join(cmds)
        assert "current.components set from storage" in full
        assert comps.get_storage() in full

    def test_with_count_uses_storage(self, mock_interp, ctx):
        item = MCSString(ctx)
        comps = MCSString(ctx)
        count = MCSNumber(ctx)
        cmds, _ = give_item(mock_interp, [item, comps, count], ctx)
        full = "\n".join(cmds)
        assert "current.count set from storage" in full
        assert count.get_storage() in full

    def test_calls_builtins_give_item(self, mock_interp, ctx):
        item = MCSString(ctx)
        cmds, _ = give_item(mock_interp, [item], ctx)
        full = "\n".join(cmds)
        assert "builtins/give_item" in full

    def test_item_storage_referenced(self, mock_interp, ctx):
        item = MCSString(ctx)
        cmds, _ = give_item(mock_interp, [item], ctx)
        full = "\n".join(cmds)
        assert item.get_storage() in full
        assert item.get_nbt() in full


# ---------------------------------------------------------------------------
# set_block()
# ---------------------------------------------------------------------------

class TestSetBlock:
    def test_returns_null(self, mock_interp, ctx):
        x = MCSNumber(ctx)
        y = MCSNumber(ctx)
        z = MCSNumber(ctx)
        block = MCSString(ctx)
        cmds, ret = set_block(mock_interp, [x, y, z, block], ctx)
        assert isinstance(ret, MCSNull)

    def test_setup_contains_x_y_z_block(self, mock_interp, ctx):
        x = MCSNumber(ctx)
        y = MCSNumber(ctx)
        z = MCSNumber(ctx)
        block = MCSString(ctx)
        cmds, _ = set_block(mock_interp, [x, y, z, block], ctx)
        full = "\n".join(cmds)
        assert "current.x set from storage" in full
        assert "current.y set from storage" in full
        assert "current.z set from storage" in full
        assert "current.block set from storage" in full

    def test_calls_builtins_set_block(self, mock_interp, ctx):
        x = MCSNumber(ctx)
        y = MCSNumber(ctx)
        z = MCSNumber(ctx)
        block = MCSString(ctx)
        cmds, _ = set_block(mock_interp, [x, y, z, block], ctx)
        full = "\n".join(cmds)
        assert "builtins/set_block" in full

    def test_each_coord_storage_is_referenced(self, mock_interp, ctx):
        x = MCSNumber(ctx)
        y = MCSNumber(ctx)
        z = MCSNumber(ctx)
        block = MCSString(ctx)
        cmds, _ = set_block(mock_interp, [x, y, z, block], ctx)
        full = "\n".join(cmds)
        assert x.get_nbt() in full
        assert y.get_nbt() in full
        assert z.get_nbt() in full
        assert block.get_nbt() in full


# ---------------------------------------------------------------------------
# concatenate()
# ---------------------------------------------------------------------------

class TestConcatenate:
    def test_returns_mcs_string(self, mock_interp, ctx):
        s1 = MCSString(ctx)
        s2 = MCSString(ctx)
        cmds, ret = concatenate(mock_interp, [s1, s2], ctx)
        assert isinstance(ret, MCSString)

    def test_setup_references_both_strings(self, mock_interp, ctx):
        s1 = MCSString(ctx)
        s2 = MCSString(ctx)
        cmds, _ = concatenate(mock_interp, [s1, s2], ctx)
        full = "\n".join(cmds)
        assert s1.get_storage() in full
        assert s2.get_storage() in full

    def test_setup_calls_macro_function(self, mock_interp, ctx):
        s1 = MCSString(ctx)
        s2 = MCSString(ctx)
        cmds, _ = concatenate(mock_interp, [s1, s2], ctx)
        full = "\n".join(cmds)
        # macro path should be referenced with "with storage"
        assert "with storage" in full

    def test_adds_macro_command_to_interpreter(self, mock_interp, ctx):
        s1 = MCSString(ctx)
        s2 = MCSString(ctx)
        concatenate(mock_interp, [s1, s2], ctx)
        mock_interp.add_command.assert_called_once()
        # Macro should contain the string_1 / string_2 macro expansions
        call_args = mock_interp.add_command.call_args
        macro_cmd = call_args[0][1]
        assert "$(string_1)$(string_2)" in macro_cmd

    def test_macro_references_output_storage(self, mock_interp, ctx):
        s1 = MCSString(ctx)
        s2 = MCSString(ctx)
        cmds, result_str = concatenate(mock_interp, [s1, s2], ctx)
        call_args = mock_interp.add_command.call_args
        macro_cmd = call_args[0][1]
        assert result_str.get_storage() in macro_cmd
        assert result_str.get_nbt() in macro_cmd


# ---------------------------------------------------------------------------
# append()
# ---------------------------------------------------------------------------

class TestAppend:
    def test_returns_null(self, mock_interp, ctx):
        lst = MCSList(ctx)
        val = MCSNumber(ctx)
        cmds, ret = append(mock_interp, [lst, val], ctx)
        assert isinstance(ret, MCSNull)

    def test_setup_references_list(self, mock_interp, ctx):
        lst = MCSList(ctx)
        val = MCSNumber(ctx)
        cmds, _ = append(mock_interp, [lst, val], ctx)
        full = "\n".join(cmds)
        assert lst.get_storage() in full
        assert lst.get_nbt() in full

    def test_setup_increments_length(self, mock_interp, ctx):
        lst = MCSList(ctx)
        val = MCSNumber(ctx)
        cmds, _ = append(mock_interp, [lst, val], ctx)
        full = "\n".join(cmds)
        assert ".length" in full
        # Should increment via scoreboard operation
        assert "mcs_math" in full

    def test_adds_macro_command_to_interpreter(self, mock_interp, ctx):
        lst = MCSList(ctx)
        val = MCSNumber(ctx)
        append(mock_interp, [lst, val], ctx)
        mock_interp.add_command.assert_called_once()
        call_args = mock_interp.add_command.call_args
        macro_cmd = call_args[0][1]
        assert "$(index)" in macro_cmd

    def test_macro_references_value_storage(self, mock_interp, ctx):
        lst = MCSList(ctx)
        val = MCSNumber(ctx)
        append(mock_interp, [lst, val], ctx)
        call_args = mock_interp.add_command.call_args
        macro_cmd = call_args[0][1]
        assert val.get_storage() in macro_cmd
        assert val.get_nbt() in macro_cmd

    def test_setup_calls_macro_with_index(self, mock_interp, ctx):
        lst = MCSList(ctx)
        val = MCSString(ctx)
        cmds, _ = append(mock_interp, [lst, val], ctx)
        full = "\n".join(cmds)
        # Should load current index from list.length
        assert "current.index set from storage" in full
        assert lst.get_nbt() + ".length" in full