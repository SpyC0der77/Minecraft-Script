"""Tests for changes in minecraft_script/compiler/compile_types.py.

This PR changed MCSObject, MCSVariable, MCSList, MCSNull to use
get_version_context() for generating storage commands instead of
hard-coded f-strings.
"""
import pytest

import minecraft_script.version_config as vc
from minecraft_script.compiler import compile_types


# ---------------------------------------------------------------------------
# Shared fake context for constructing MCS objects in tests
# ---------------------------------------------------------------------------

class FakeContext:
    """Minimal context object that satisfies compile_types requirements."""
    def __init__(self, uuid: str = "deadbeef-0000-0000-0000-000000000001"):
        self.uuid = uuid


FAKE_UUID_1 = "deadbeef-0000-0000-0000-000000000001"
FAKE_UUID_2 = "cafef00d-0000-0000-0000-000000000002"


@pytest.fixture(autouse=True)
def version_context_1204():
    """Ensure the 1.20.4 version context is active for all tests in this file."""
    ctx = vc.init_version_context("test_pack")
    yield ctx
    vc.clear_version_context()


# ===========================================================================
# MCSObject
# ===========================================================================

class TestMCSObjectStorageCommands:
    """Tests for MCSObject methods changed in this PR."""

    def test_get_storage_returns_mcs_prefix_plus_uuid(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSNumber(ctx)
        assert obj.get_storage() == f"mcs_{FAKE_UUID_1}"

    def test_get_nbt_contains_storage_compartment(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSNumber(ctx)
        assert obj.get_nbt().startswith("number.")

    def test_save_to_storage_cmd_returns_string(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSNumber(ctx)
        cmd = obj.save_to_storage_cmd(42)
        assert isinstance(cmd, str)

    def test_save_to_storage_cmd_contains_storage(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSNumber(ctx)
        cmd = obj.save_to_storage_cmd(42)
        assert obj.get_storage() in cmd

    def test_save_to_storage_cmd_contains_nbt(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSNumber(ctx)
        cmd = obj.save_to_storage_cmd(42)
        assert obj.get_nbt() in cmd

    def test_save_to_storage_cmd_contains_value(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSNumber(ctx)
        cmd = obj.save_to_storage_cmd(99)
        assert "99" in cmd

    def test_save_to_storage_cmd_uses_data_modify(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSNumber(ctx)
        cmd = obj.save_to_storage_cmd(1)
        assert "data modify storage" in cmd

    def test_delete_from_storage_cmd_returns_string(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSNumber(ctx)
        cmd = obj.delete_from_storage_cmd()
        assert isinstance(cmd, str)

    def test_delete_from_storage_cmd_contains_data_remove(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSNumber(ctx)
        cmd = obj.delete_from_storage_cmd()
        assert "data remove storage" in cmd

    def test_delete_from_storage_cmd_contains_storage(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSNumber(ctx)
        cmd = obj.delete_from_storage_cmd()
        assert obj.get_storage() in cmd

    def test_delete_from_storage_cmd_contains_nbt(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSNumber(ctx)
        cmd = obj.delete_from_storage_cmd()
        assert obj.get_nbt() in cmd

    def test_set_to_current_cmd_returns_string(self):
        ctx1 = FakeContext(FAKE_UUID_1)
        ctx2 = FakeContext(FAKE_UUID_2)
        obj = compile_types.MCSNumber(ctx1)
        cmd = obj.set_to_current_cmd(ctx2)
        assert isinstance(cmd, str)

    def test_set_to_current_cmd_contains_dest_storage(self):
        ctx1 = FakeContext(FAKE_UUID_1)
        ctx2 = FakeContext(FAKE_UUID_2)
        obj = compile_types.MCSNumber(ctx1)
        cmd = obj.set_to_current_cmd(ctx2)
        assert f"mcs_{FAKE_UUID_2}" in cmd

    def test_set_to_current_cmd_contains_source_storage(self):
        ctx1 = FakeContext(FAKE_UUID_1)
        ctx2 = FakeContext(FAKE_UUID_2)
        obj = compile_types.MCSNumber(ctx1)
        cmd = obj.set_to_current_cmd(ctx2)
        assert f"mcs_{FAKE_UUID_1}" in cmd

    def test_set_to_current_cmd_references_current_key(self):
        ctx1 = FakeContext(FAKE_UUID_1)
        ctx2 = FakeContext(FAKE_UUID_2)
        obj = compile_types.MCSNumber(ctx1)
        cmd = obj.set_to_current_cmd(ctx2)
        assert "current" in cmd

    def test_set_to_current_cmd_uses_data_modify(self):
        ctx1 = FakeContext(FAKE_UUID_1)
        ctx2 = FakeContext(FAKE_UUID_2)
        obj = compile_types.MCSNumber(ctx1)
        cmd = obj.set_to_current_cmd(ctx2)
        assert "data modify storage" in cmd


# ===========================================================================
# MCSVariable
# ===========================================================================

class TestMCSVariable:
    def test_get_nbt_uses_variable_prefix(self):
        ctx = FakeContext(FAKE_UUID_1)
        var = compile_types.MCSVariable("my_var", ctx)
        assert var.get_nbt() == "variable.my_var"

    def test_get_storage_uses_context_uuid(self):
        ctx = FakeContext(FAKE_UUID_1)
        var = compile_types.MCSVariable("x", ctx)
        assert var.get_storage() == f"mcs_{FAKE_UUID_1}"

    def test_set_to_current_cmd_returns_string(self):
        ctx1 = FakeContext(FAKE_UUID_1)
        ctx2 = FakeContext(FAKE_UUID_2)
        var = compile_types.MCSVariable("myvar", ctx1)
        cmd = var.set_to_current_cmd(ctx2)
        assert isinstance(cmd, str)

    def test_set_to_current_cmd_references_dest_storage(self):
        ctx1 = FakeContext(FAKE_UUID_1)
        ctx2 = FakeContext(FAKE_UUID_2)
        var = compile_types.MCSVariable("myvar", ctx1)
        cmd = var.set_to_current_cmd(ctx2)
        assert f"mcs_{FAKE_UUID_2}" in cmd

    def test_set_to_current_cmd_references_variable_nbt(self):
        ctx1 = FakeContext(FAKE_UUID_1)
        ctx2 = FakeContext(FAKE_UUID_2)
        var = compile_types.MCSVariable("myvar", ctx1)
        cmd = var.set_to_current_cmd(ctx2)
        assert "variable.myvar" in cmd

    def test_set_to_current_uses_data_modify(self):
        ctx1 = FakeContext(FAKE_UUID_1)
        ctx2 = FakeContext(FAKE_UUID_2)
        var = compile_types.MCSVariable("v", ctx1)
        cmd = var.set_to_current_cmd(ctx2)
        assert "data modify storage" in cmd


# ===========================================================================
# MCSNull
# ===========================================================================

class TestMCSNull:
    def test_save_to_storage_cmd_returns_string(self):
        ctx = FakeContext(FAKE_UUID_1)
        null = compile_types.MCSNull(ctx)
        cmd = null.save_to_storage_cmd()
        assert isinstance(cmd, str)

    def test_save_to_storage_cmd_contains_null_value(self):
        ctx = FakeContext(FAKE_UUID_1)
        null = compile_types.MCSNull(ctx)
        cmd = null.save_to_storage_cmd()
        assert "0b" in cmd

    def test_save_to_storage_cmd_uses_data_modify(self):
        ctx = FakeContext(FAKE_UUID_1)
        null = compile_types.MCSNull(ctx)
        cmd = null.save_to_storage_cmd()
        assert "data modify storage" in cmd

    def test_set_to_current_cmd_returns_string(self):
        ctx1 = FakeContext(FAKE_UUID_1)
        ctx2 = FakeContext(FAKE_UUID_2)
        null = compile_types.MCSNull(ctx1)
        cmd = null.set_to_current_cmd(ctx2)
        assert isinstance(cmd, str)

    def test_set_to_current_cmd_sets_to_null(self):
        ctx1 = FakeContext(FAKE_UUID_1)
        ctx2 = FakeContext(FAKE_UUID_2)
        null = compile_types.MCSNull(ctx1)
        cmd = null.set_to_current_cmd(ctx2)
        assert "0b" in cmd

    def test_set_to_current_cmd_targets_dest_storage(self):
        ctx1 = FakeContext(FAKE_UUID_1)
        ctx2 = FakeContext(FAKE_UUID_2)
        null = compile_types.MCSNull(ctx1)
        cmd = null.set_to_current_cmd(ctx2)
        assert f"mcs_{FAKE_UUID_2}" in cmd

    def test_set_to_current_cmd_targets_current_nbt(self):
        ctx1 = FakeContext(FAKE_UUID_1)
        ctx2 = FakeContext(FAKE_UUID_2)
        null = compile_types.MCSNull(ctx1)
        cmd = null.set_to_current_cmd(ctx2)
        assert "current" in cmd

    def test_repr(self):
        ctx = FakeContext(FAKE_UUID_1)
        null = compile_types.MCSNull(ctx)
        assert repr(null) == "MCSNull()"


# ===========================================================================
# MCSList
# ===========================================================================

class TestMCSList:
    def _make_simple_element(self, ctx, value=42):
        """Create a MCSNumber element with a save command."""
        elem = compile_types.MCSNumber(ctx)
        return elem

    def test_save_to_storage_cmd_returns_list(self):
        ctx = FakeContext(FAKE_UUID_1)
        lst = compile_types.MCSList(ctx)
        cmds = lst.save_to_storage_cmd([])
        assert isinstance(cmds, list)

    def test_save_empty_list_has_length_zero(self):
        ctx = FakeContext(FAKE_UUID_1)
        lst = compile_types.MCSList(ctx)
        cmds = lst.save_to_storage_cmd([])
        # First command sets the length
        assert "length" in cmds[0]
        assert "0" in cmds[0]

    def test_save_list_length_command_is_first(self):
        ctx = FakeContext(FAKE_UUID_1)
        lst = compile_types.MCSList(ctx)
        elem = compile_types.MCSNumber(ctx)
        cmds = lst.save_to_storage_cmd([elem])
        assert "length" in cmds[0]

    def test_save_list_with_elements_produces_commands(self):
        ctx = FakeContext(FAKE_UUID_1)
        lst = compile_types.MCSList(ctx)
        elem1 = compile_types.MCSNumber(ctx)
        elem2 = compile_types.MCSString(ctx)
        cmds = lst.save_to_storage_cmd([elem1, elem2])
        # length + 2*(set_to_current + element) = 5 total
        assert len(cmds) == 5

    def test_save_list_element_references_index_zero(self):
        ctx = FakeContext(FAKE_UUID_1)
        lst = compile_types.MCSList(ctx)
        elem = compile_types.MCSNumber(ctx)
        cmds = lst.save_to_storage_cmd([elem])
        # One of the commands should reference ".0"
        assert any(".0" in cmd for cmd in cmds)

    def test_save_list_element_command_uses_data_modify(self):
        ctx = FakeContext(FAKE_UUID_1)
        lst = compile_types.MCSList(ctx)
        elem = compile_types.MCSNumber(ctx)
        cmds = lst.save_to_storage_cmd([elem])
        assert all("data modify" in cmd or "data remove" in cmd for cmd in cmds if cmd)

    def test_save_list_length_uses_version_template(self):
        ctx = FakeContext(FAKE_UUID_1)
        lst = compile_types.MCSList(ctx)
        cmds = lst.save_to_storage_cmd([])
        # Template renders: data modify storage <storage> <nbt>.length set value <len>
        assert "data modify storage" in cmds[0]
        assert ".length" in cmds[0]

    def test_repr(self):
        ctx = FakeContext(FAKE_UUID_1)
        lst = compile_types.MCSList(ctx)
        assert "MCSList" in repr(lst)


# ===========================================================================
# Various MCS types: storage compartments
# ===========================================================================

class TestMCSTypeCompartments:
    """Verify each type uses the right storage compartment."""

    def test_mcs_number_compartment(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSNumber(ctx)
        assert obj.get_nbt().startswith("number.")

    def test_mcs_string_compartment(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSString(ctx)
        assert obj.get_nbt().startswith("string.")

    def test_mcs_boolean_compartment(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSBoolean(ctx)
        assert obj.get_nbt().startswith("boolean.")

    def test_mcs_unknown_compartment(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSUnknown(ctx)
        assert obj.get_nbt().startswith("unknown.")

    def test_mcs_null_compartment(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSNull(ctx)
        assert obj.get_nbt().startswith("null.")

    def test_mcs_list_compartment(self):
        ctx = FakeContext(FAKE_UUID_1)
        obj = compile_types.MCSList(ctx)
        assert obj.get_nbt().startswith("list.")