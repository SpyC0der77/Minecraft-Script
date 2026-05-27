"""Tests for changes in minecraft_script/compiler/compile_interpreter.py.

This PR changed:
- add_comment(): now preserves list->tuple conversion even when debug_comments=False,
  and handles list input for the prefix case.
"""
import pytest
from unittest.mock import patch

import minecraft_script.version_config as vc
from minecraft_script.common import COMMON_CONFIG


def _setup_version_ctx():
    """Helper: ensure a version context exists for tests that indirectly need it."""
    if vc._version_ctx is None:
        vc.init_version_context("test_dp")


# ---------------------------------------------------------------------------
# Tests for add_comment()
# ---------------------------------------------------------------------------

class TestAddComment:
    """Tests for the add_comment() function changed in this PR."""

    @pytest.fixture(autouse=True)
    def enable_debug_comments(self):
        original = COMMON_CONFIG.get("debug_comments")
        COMMON_CONFIG["debug_comments"] = True
        yield
        COMMON_CONFIG["debug_comments"] = original

    def _get_add_comment(self):
        from minecraft_script.compiler.compile_interpreter import add_comment
        return add_comment

    # ---- debug_comments = True ----

    def test_tuple_input_prepends_comment(self):
        add_comment = self._get_add_comment()
        result = add_comment(("cmd1", "cmd2"), "my comment")
        assert result[0] == "\n# my comment"
        assert "cmd1" in result
        assert "cmd2" in result

    def test_string_input_prepends_comment(self):
        add_comment = self._get_add_comment()
        result = add_comment("single cmd", "my comment")
        assert result.startswith("\n# my comment\n")
        assert "single cmd" in result

    def test_list_input_becomes_tuple_with_comment(self):
        add_comment = self._get_add_comment()
        result = add_comment(["cmd1", "cmd2"], "a comment")
        assert isinstance(result, tuple)
        assert result[0] == "\n# a comment"
        assert "cmd1" in result
        assert "cmd2" in result

    def test_list_input_returns_tuple_not_list(self):
        add_comment = self._get_add_comment()
        result = add_comment(["a", "b"], "comment")
        assert isinstance(result, tuple)

    # ---- debug_comments = False ----

    def test_tuple_returned_unchanged_when_debug_off(self):
        add_comment = self._get_add_comment()
        COMMON_CONFIG["debug_comments"] = False
        cmds = ("cmd1", "cmd2")
        result = add_comment(cmds, "ignored")
        assert result == cmds

    def test_string_returned_unchanged_when_debug_off(self):
        add_comment = self._get_add_comment()
        COMMON_CONFIG["debug_comments"] = False
        result = add_comment("single cmd", "ignored")
        assert result == "single cmd"

    def test_list_converted_to_tuple_when_debug_off(self):
        """PR change: list input is now converted to tuple even when debug is off."""
        add_comment = self._get_add_comment()
        COMMON_CONFIG["debug_comments"] = False
        result = add_comment(["a", "b"], "ignored comment")
        assert isinstance(result, tuple)
        assert result == ("a", "b")

    def test_list_debug_off_preserves_content(self):
        add_comment = self._get_add_comment()
        COMMON_CONFIG["debug_comments"] = False
        result = add_comment(["x", "y", "z"], "ignored")
        assert list(result) == ["x", "y", "z"]

    # ---- error cases ----

    def test_raises_value_error_for_non_iterable_input(self):
        add_comment = self._get_add_comment()
        with pytest.raises(ValueError) as exc_info:
            add_comment(42, "comment")
        assert "tuple, list, or str" in str(exc_info.value)

    def test_raises_value_error_for_dict_input(self):
        add_comment = self._get_add_comment()
        with pytest.raises(ValueError):
            add_comment({"key": "val"}, "comment")

    def test_raises_value_error_for_none_input(self):
        add_comment = self._get_add_comment()
        with pytest.raises(ValueError):
            add_comment(None, "comment")

    def test_empty_tuple_with_comment(self):
        add_comment = self._get_add_comment()
        result = add_comment((), "comment")
        assert result == ("\n# comment",)

    def test_empty_list_with_comment(self):
        add_comment = self._get_add_comment()
        result = add_comment([], "comment")
        assert isinstance(result, tuple)
        assert result == ("\n# comment",)

    def test_empty_string_with_comment(self):
        add_comment = self._get_add_comment()
        result = add_comment("", "comment")
        assert result.startswith("\n# comment\n")