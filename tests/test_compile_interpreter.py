"""
Tests for changed parts of minecraft_script/compiler/compile_interpreter.py

Covers: add_comment (list->tuple fix), init_version_context lifecycle inside
mcs_compile, CompileContext structure.
"""
import pytest
from unittest.mock import patch

import minecraft_script.version_config as vc
from minecraft_script.common import COMMON_CONFIG
from minecraft_script.compiler.compile_interpreter import (
    add_comment, CompileContext, CompileCommands, CompileResult
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def debug_on(version_ctx_1204):
    """Ensure debug_comments is True."""
    old = COMMON_CONFIG.get("debug_comments")
    COMMON_CONFIG["debug_comments"] = True
    yield
    COMMON_CONFIG["debug_comments"] = old


@pytest.fixture
def debug_off(version_ctx_1204):
    """Ensure debug_comments is False."""
    old = COMMON_CONFIG.get("debug_comments")
    COMMON_CONFIG["debug_comments"] = False
    yield
    COMMON_CONFIG["debug_comments"] = old


# ---------------------------------------------------------------------------
# add_comment
# ---------------------------------------------------------------------------

class TestAddComment:
    def test_tuple_input_debug_on_prepends_comment(self, debug_on):
        result = add_comment(("cmd1", "cmd2"), "my comment")
        assert isinstance(result, tuple)
        assert result[0] == "\n# my comment"
        assert result[1] == "cmd1"
        assert result[2] == "cmd2"

    def test_list_input_debug_on_converts_to_tuple_and_prepends(self, debug_on):
        result = add_comment(["cmd1", "cmd2"], "list comment")
        assert isinstance(result, tuple)
        assert result[0] == "\n# list comment"
        assert "cmd1" in result
        assert "cmd2" in result

    def test_str_input_debug_on_prepends_comment(self, debug_on):
        result = add_comment("single_cmd", "str comment")
        assert isinstance(result, str)
        assert "# str comment" in result
        assert "single_cmd" in result

    def test_tuple_input_debug_off_returns_unchanged(self, debug_off):
        original = ("cmd1", "cmd2")
        result = add_comment(original, "ignored")
        assert result == original

    def test_list_input_debug_off_converts_to_tuple(self, debug_off):
        original = ["cmd1", "cmd2"]
        result = add_comment(original, "ignored")
        assert isinstance(result, tuple)
        assert result == ("cmd1", "cmd2")

    def test_str_input_debug_off_returns_unchanged(self, debug_off):
        result = add_comment("single_cmd", "ignored")
        assert result == "single_cmd"

    def test_invalid_type_raises_value_error(self, debug_on):
        with pytest.raises(ValueError, match="Commands have to be tuple, list, or str"):
            add_comment(42, "comment")

    def test_invalid_type_none_raises_value_error(self, debug_on):
        with pytest.raises(ValueError):
            add_comment(None, "comment")

    def test_empty_tuple_debug_on(self, debug_on):
        result = add_comment((), "empty")
        assert isinstance(result, tuple)
        assert result == ("\n# empty",)

    def test_empty_list_debug_on(self, debug_on):
        result = add_comment([], "empty list")
        assert isinstance(result, tuple)
        assert result[0] == "\n# empty list"

    def test_empty_list_debug_off_returns_empty_tuple(self, debug_off):
        result = add_comment([], "ignored")
        assert result == ()


# ---------------------------------------------------------------------------
# CompileContext
# ---------------------------------------------------------------------------

class TestCompileContext:
    def test_top_level_context_has_builtins(self, version_ctx_1204):
        ctx = CompileContext("init", top_level=True)
        # Check that builtin functions are loaded
        assert ctx.symbols.symbols.get("log") is not None or ctx.get("log") is not None

    def test_context_has_unique_uuid(self, version_ctx_1204):
        ctx1 = CompileContext("fn1")
        ctx2 = CompileContext("fn2")
        assert ctx1.uuid != ctx2.uuid

    def test_mcfunction_name_user_functions(self, version_ctx_1204):
        ctx = CompileContext("my_fn")
        assert ctx.mcfunction_name == "user_functions/my_fn"

    def test_mcfunction_name_code_blocks(self, version_ctx_1204):
        # No name -> code block
        ctx = CompileContext()
        assert ctx.mcfunction_name.startswith("code_blocks/cb_")

    def test_child_context_has_parent_ref(self, version_ctx_1204):
        parent = CompileContext("parent")
        child = CompileContext(parent=parent)
        assert child.parent is parent

    def test_declare_and_get(self, version_ctx_1204):
        from minecraft_script.compiler.compile_types import MCSNumber
        ctx = CompileContext("test")
        num = MCSNumber(ctx)
        ctx.declare("myvar", num)
        assert ctx.get("myvar") is num

    def test_get_context_ownership_finds_self(self, version_ctx_1204):
        from minecraft_script.compiler.compile_types import MCSNumber
        ctx = CompileContext("owner")
        num = MCSNumber(ctx)
        ctx.declare("owned_var", num)
        assert ctx.get_context_ownership("owned_var") is ctx

    def test_get_context_ownership_traverses_parent(self, version_ctx_1204):
        from minecraft_script.compiler.compile_types import MCSNumber
        parent = CompileContext("parent")
        child = CompileContext(parent=parent)
        num = MCSNumber(parent)
        parent.declare("parent_var", num)
        assert child.get_context_ownership("parent_var") is parent

    def test_undefined_var_raises_name_error(self, version_ctx_1204):
        ctx = CompileContext("test")
        with pytest.raises(NameError):
            ctx.get_context_ownership("undefined_var")


# ---------------------------------------------------------------------------
# CompileCommands
# ---------------------------------------------------------------------------

class TestCompileCommands:
    def test_add_command_and_get_file_content(self):
        cmds = CompileCommands()
        cmds.add_command("fn1", "cmd_a")
        cmds.add_command("fn1", "cmd_b")
        content = cmds.get_file_content("fn1")
        assert "cmd_a" in content
        assert "cmd_b" in content

    def test_get_mcs_functions(self):
        cmds = CompileCommands()
        cmds.add_command("fn1", "cmd1")
        cmds.add_command("fn2", "cmd2")
        fns = cmds.get_mcs_functions()
        assert "fn1" in fns
        assert "fn2" in fns

    def test_empty_function_returns_empty_string(self):
        cmds = CompileCommands()
        assert cmds.get_file_content("nonexistent") == ""

    def test_commands_joined_with_newline(self):
        cmds = CompileCommands()
        cmds.add_command("fn", "line1")
        cmds.add_command("fn", "line2")
        content = cmds.get_file_content("fn")
        assert content == "line1\nline2"


# ---------------------------------------------------------------------------
# CompileResult
# ---------------------------------------------------------------------------

class TestCompileResult:
    def test_default_value_is_none(self):
        result = CompileResult()
        assert result.get_value() is None

    def test_default_return_is_none(self):
        result = CompileResult()
        assert result.get_return() is None

    def test_value_is_returned(self, version_ctx_1204):
        from minecraft_script.compiler.compile_types import MCSNumber
        ctx = CompileContext("fn")
        num = MCSNumber(ctx)
        result = CompileResult(value=num)
        assert result.get_value() is num

    def test_return_value_is_returned(self, version_ctx_1204):
        from minecraft_script.compiler.compile_types import MCSString
        ctx = CompileContext("fn")
        s = MCSString(ctx)
        result = CompileResult(return_value=s)
        assert result.get_return() is s


# ---------------------------------------------------------------------------
# init_version_context in mcs_compile
# ---------------------------------------------------------------------------

class TestMcsCompileVersionContextLifecycle:
    """Verify that mcs_compile initialises the version context with the datapack_id."""

    def test_init_called_with_datapack_id(self):
        from minecraft_script.compiler.compile_interpreter import mcs_compile
        import tempfile
        import minecraft_script.compiler.compile_interpreter as ci

        captured = {}

        original_init = vc.init_version_context
        def fake_init(datapack_id):
            captured["datapack_id"] = datapack_id
            return original_init(datapack_id)

        # Patch the name as it is imported inside compile_interpreter
        with patch.object(ci, "init_version_context", side_effect=fake_init):
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    mcs_compile([], tmp, "my_datapack")
            except Exception:
                pass  # compilation may fail on empty AST - that's ok

        assert captured.get("datapack_id") == "my_datapack"