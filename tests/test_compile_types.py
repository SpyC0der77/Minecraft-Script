"""
Tests for minecraft_script/compiler/compile_types.py

Covers: MCSObject, MCSVariable, MCSList, MCSNull, MCSNumber, MCSString,
MCSBoolean, MCSUnknown, MCSFunction - focusing on the version-context-based
command generation introduced in this PR.
"""
import pytest
from unittest.mock import MagicMock

import minecraft_script.version_config as vc
from minecraft_script.version_config import init_version_context
from minecraft_script.compiler.compile_types import (
    MCSObject, MCSVariable, MCSList, MCSNull,
    MCSNumber, MCSString, MCSBoolean, MCSUnknown,
    MCSFunction,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ctx(version_ctx_1204):
    """Return a minimal CompileContext-like mock for use in type construction."""
    from minecraft_script.compiler.compile_interpreter import CompileContext
    return CompileContext("test_fn", top_level=True)


@pytest.fixture
def ctx2(version_ctx_1204):
    """Return a second CompileContext for set_to_current_cmd tests."""
    from minecraft_script.compiler.compile_interpreter import CompileContext
    return CompileContext("test_fn2", top_level=True)


# ---------------------------------------------------------------------------
# MCSObject
# ---------------------------------------------------------------------------

class TestMCSObject:
    def test_get_nbt_format(self, ctx):
        obj = MCSObject(ctx, "number")
        assert obj.get_nbt().startswith("number.")
        assert len(obj.get_nbt()) > len("number.")

    def test_get_storage_format(self, ctx):
        obj = MCSObject(ctx, "string")
        storage = obj.get_storage()
        assert storage.startswith("mcs_")
        assert ctx.uuid in storage

    def test_save_to_storage_cmd_literal_42(self, ctx):
        obj = MCSObject(ctx, "number")
        cmd = obj.save_to_storage_cmd(42)
        assert "data modify storage" in cmd
        assert obj.get_storage() in cmd
        assert obj.get_nbt() in cmd
        assert "42" in cmd

    def test_save_to_storage_cmd_literal_bytes(self, ctx):
        obj = MCSObject(ctx, "string")
        cmd = obj.save_to_storage_cmd("0b")
        assert "set value" in cmd
        assert "0b" in cmd

    def test_delete_from_storage_cmd(self, ctx):
        obj = MCSObject(ctx, "number")
        cmd = obj.delete_from_storage_cmd()
        assert "data remove storage" in cmd
        assert obj.get_storage() in cmd
        assert obj.get_nbt() in cmd

    def test_set_to_current_cmd(self, ctx, ctx2):
        obj = MCSObject(ctx, "string")
        cmd = obj.set_to_current_cmd(ctx2)
        assert "data modify storage" in cmd
        assert f"mcs_{ctx2.uuid}" in cmd
        assert "current" in cmd
        assert obj.get_storage() in cmd
        assert obj.get_nbt() in cmd

    def test_each_object_has_unique_uuid(self, ctx):
        obj1 = MCSObject(ctx, "number")
        obj2 = MCSObject(ctx, "number")
        assert obj1.uuid != obj2.uuid

    def test_storage_compartment_in_nbt(self, ctx):
        obj = MCSObject(ctx, "boolean")
        assert "boolean" in obj.get_nbt()


# ---------------------------------------------------------------------------
# MCSVariable
# ---------------------------------------------------------------------------

class TestMCSVariable:
    def test_get_nbt_includes_variable_prefix(self, ctx):
        var = MCSVariable("x", ctx)
        assert var.get_nbt() == "variable.x"

    def test_get_storage_matches_context(self, ctx):
        var = MCSVariable("y", ctx)
        assert var.get_storage() == f"mcs_{ctx.uuid}"

    def test_set_to_current_cmd_is_correct(self, ctx, ctx2):
        var = MCSVariable("my_var", ctx)
        cmd = var.set_to_current_cmd(ctx2)
        assert "data modify storage" in cmd
        assert f"mcs_{ctx2.uuid}" in cmd
        assert "current" in cmd
        assert "variable.my_var" in cmd

    def test_repr(self, ctx):
        var = MCSVariable("z", ctx)
        r = repr(var)
        assert "MCSVariable" in r
        assert "z" in r

    def test_different_names_yield_different_nbts(self, ctx):
        var1 = MCSVariable("alpha", ctx)
        var2 = MCSVariable("beta", ctx)
        assert var1.get_nbt() != var2.get_nbt()


# ---------------------------------------------------------------------------
# MCSNull
# ---------------------------------------------------------------------------

class TestMCSNull:
    def test_save_to_storage_cmd_uses_0b(self, ctx):
        null = MCSNull(ctx)
        cmd = null.save_to_storage_cmd()
        assert "0b" in cmd
        assert "data modify storage" in cmd

    def test_set_to_current_cmd_uses_0b(self, ctx, ctx2):
        null = MCSNull(ctx)
        cmd = null.set_to_current_cmd(ctx2)
        assert "0b" in cmd
        assert f"mcs_{ctx2.uuid}" in cmd
        assert "current" in cmd

    def test_repr(self, ctx):
        null = MCSNull(ctx)
        assert repr(null) == "MCSNull()"

    def test_storage_compartment_is_null(self, ctx):
        null = MCSNull(ctx)
        assert "null" in null.get_nbt()


# ---------------------------------------------------------------------------
# MCSNumber
# ---------------------------------------------------------------------------

class TestMCSNumber:
    def test_nbt_starts_with_number(self, ctx):
        num = MCSNumber(ctx)
        assert num.get_nbt().startswith("number.")

    def test_repr(self, ctx):
        num = MCSNumber(ctx)
        assert "MCSNumber" in repr(num)

    def test_delete_cmd_removes_storage(self, ctx):
        num = MCSNumber(ctx)
        cmd = num.delete_from_storage_cmd()
        assert "data remove storage" in cmd
        assert num.get_nbt() in cmd


# ---------------------------------------------------------------------------
# MCSString
# ---------------------------------------------------------------------------

class TestMCSString:
    def test_nbt_starts_with_string(self, ctx):
        s = MCSString(ctx)
        assert s.get_nbt().startswith("string.")

    def test_repr(self, ctx):
        s = MCSString(ctx)
        assert "MCSString" in repr(s)

    def test_save_cmd_uses_string_compartment(self, ctx):
        s = MCSString(ctx)
        cmd = s.save_to_storage_cmd('"test"')
        assert "string." in cmd


# ---------------------------------------------------------------------------
# MCSBoolean
# ---------------------------------------------------------------------------

class TestMCSBoolean:
    def test_nbt_starts_with_boolean(self, ctx):
        b = MCSBoolean(ctx)
        assert b.get_nbt().startswith("boolean.")

    def test_repr(self, ctx):
        b = MCSBoolean(ctx)
        assert "MCSBoolean" in repr(b)


# ---------------------------------------------------------------------------
# MCSUnknown
# ---------------------------------------------------------------------------

class TestMCSUnknown:
    def test_nbt_starts_with_unknown(self, ctx):
        u = MCSUnknown(ctx)
        assert u.get_nbt().startswith("unknown.")

    def test_repr(self, ctx):
        u = MCSUnknown(ctx)
        assert "MCSUnknown" in repr(u)


# ---------------------------------------------------------------------------
# MCSList
# ---------------------------------------------------------------------------

class TestMCSList:
    def test_nbt_starts_with_list(self, ctx):
        lst = MCSList(ctx)
        assert lst.get_nbt().startswith("list.")

    def test_repr(self, ctx):
        lst = MCSList(ctx)
        assert "MCSList" in repr(lst)

    def test_save_to_storage_cmd_empty_list(self, ctx):
        lst = MCSList(ctx)
        cmds = lst.save_to_storage_cmd([])
        assert isinstance(cmds, list)
        # Should still have the length command
        assert len(cmds) == 1
        assert ".length set value 0" in cmds[0]

    def test_save_to_storage_cmd_single_element(self, ctx):
        lst = MCSList(ctx)
        elem = MCSNumber(ctx)
        cmds = lst.save_to_storage_cmd([elem])
        assert isinstance(cmds, list)
        # length cmd + (set_to_current_cmd + element cmd per item)
        assert len(cmds) == 3  # length + current + element
        assert ".length set value 1" in cmds[0]

    def test_save_to_storage_cmd_multiple_elements(self, ctx):
        lst = MCSList(ctx)
        elems = [MCSNumber(ctx), MCSString(ctx), MCSBoolean(ctx)]
        cmds = lst.save_to_storage_cmd(elems)
        assert isinstance(cmds, list)
        # 1 length + 3 * (1 set_to_current + 1 element) = 7
        assert len(cmds) == 7
        assert ".length set value 3" in cmds[0]

    def test_save_to_storage_cmd_element_indices(self, ctx):
        lst = MCSList(ctx)
        elems = [MCSNumber(ctx), MCSString(ctx)]
        cmds = lst.save_to_storage_cmd(elems)
        # Check index 0 and 1 appear in the element commands
        full = "\n".join(cmds)
        nbt = lst.get_nbt()
        assert f"{nbt}.0" in full
        assert f"{nbt}.1" in full


# ---------------------------------------------------------------------------
# MCSFunction.call
# ---------------------------------------------------------------------------

class TestMCSFunction:
    def test_call_with_no_params_returns_null_and_invoke(self, ctx, version_ctx_1204):
        """A function with no parameters should return an invoke command only."""
        from minecraft_script.compiler.compile_interpreter import CompileContext
        local_ctx = CompileContext("my_fn")

        fnc = MCSFunction.__new__(MCSFunction)
        fnc.name = "my_fn"
        fnc.parameter_names = []
        fnc.local_context = local_ctx

        mock_interp = MagicMock()
        mock_interp.datapack_id = "test_pack"

        cmds, ret = fnc.call(mock_interp, [], ctx)
        assert isinstance(ret, MCSNull)
        assert len(cmds) == 1
        assert "user_functions/my_fn" in cmds[0]

    def test_call_with_one_param_has_setup_and_invoke(self, ctx, version_ctx_1204):
        """A function with one parameter should have param setup lines + invoke."""
        from minecraft_script.compiler.compile_interpreter import CompileContext
        local_ctx = CompileContext("fn_with_param")

        fnc = MCSFunction.__new__(MCSFunction)
        fnc.name = "fn_with_param"
        fnc.parameter_names = ["arg0"]
        fnc.local_context = local_ctx

        arg = MCSNumber(ctx)
        mock_interp = MagicMock()
        mock_interp.datapack_id = "test_pack"

        cmds, ret = fnc.call(mock_interp, [arg], ctx)
        assert isinstance(ret, MCSNull)
        # 2 param setup lines + 1 invoke = 3 total
        assert len(cmds) == 3
        assert "user_functions/fn_with_param" in cmds[-1]

    def test_call_param_references_argument_storage(self, ctx, version_ctx_1204):
        from minecraft_script.compiler.compile_interpreter import CompileContext
        local_ctx = CompileContext("fn_param_check")

        fnc = MCSFunction.__new__(MCSFunction)
        fnc.name = "fn_param_check"
        fnc.parameter_names = ["myarg"]
        fnc.local_context = local_ctx

        arg = MCSString(ctx)
        mock_interp = MagicMock()
        mock_interp.datapack_id = "test_pack"

        cmds, _ = fnc.call(mock_interp, [arg], ctx)
        # The param setup should reference the argument storage/nbt
        setup_cmds = "\n".join(cmds[:-1])
        assert arg.get_storage() in setup_cmds
        assert "myarg" in setup_cmds

    def test_repr(self, ctx):
        from minecraft_script.compiler.compile_interpreter import CompileContext
        local_ctx = CompileContext("test_fn_repr")
        fnc = MCSFunction.__new__(MCSFunction)
        fnc.name = "test_fn_repr"
        fnc.parameter_names = []
        fnc.local_context = local_ctx
        assert "MCSFunction" in repr(fnc)
        assert "test_fn_repr" in repr(fnc)