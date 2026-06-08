import pytest

from minecraft_script.errors import MCSIllegalCharacterError, MCSSyntaxError
from tests._parse_helpers import token_types, token_values, tokenize


def test_tokenizes_numbers():
    tokens = tokenize("0 42 3.14")
    assert token_types("0 42 3.14") == ["TT_NUMBER", "TT_NUMBER", "TT_NUMBER", "TT_DOT", "TT_NUMBER"]
    assert [token.value for token in tokens] == ["0", "42", "3", ".", "14"]


def test_tokenizes_strings_with_single_and_double_quotes():
    assert token_values('"hello" \'world\'') == ["hello", "world"]
    assert token_types('"hello" \'world\'') == ["TT_STRING", "TT_STRING"]


def test_tokenizes_keywords_and_generic_names():
    assert token_types("var function while async import") == [
        "TT_VAR_DEFINE",
        "TT_FUNC_DEFINE",
        "TT_WHILE_LOOP",
        "TT_ASYNC",
        "TT_IMPORT",
    ]
    assert token_types("my_function helper_value") == ["TT_NAME", "TT_NAME"]


def test_tokenizes_boolean_and_null_literals():
    assert token_types("true false null") == ["TT_BOOLEAN", "TT_BOOLEAN", "TT_NULL"]


def test_tokenizes_entity_selector_with_bracket_arguments():
    code = '@a[type=minecraft:pig,distance=..5] say "hi"'
    types = token_types(code)
    assert types[0] == "TT_SELECTOR"
    assert token_values(code)[0] == '@a[type=minecraft:pig,distance=..5]'


def test_tokenizes_entity_selector_with_nested_brackets():
    code = '@e[nbt={foo:[1,2]}] log("ok")'
    assert token_types(code)[0] == "TT_SELECTOR"
    assert token_values(code)[0] == '@e[nbt={foo:[1,2]}]'


def test_ignores_line_comments():
    assert token_types('var x = 1; // comment\nvar y = 2;') == [
        "TT_VAR_DEFINE",
        "TT_NAME",
        "TT_EQUALS",
        "TT_NUMBER",
        "TT_NEWLINE",
        "TT_VAR_DEFINE",
        "TT_NAME",
        "TT_EQUALS",
        "TT_NUMBER",
        "TT_NEWLINE",
    ]


def test_raises_for_illegal_character():
    with pytest.raises(MCSIllegalCharacterError, match="Illegal Character: #"):
        tokenize("# not a comment in MCS")


def test_raises_for_unmatched_string():
    with pytest.raises(MCSSyntaxError, match="Unmatched string"):
        tokenize('var x = "unfinished')


def test_raises_for_malformed_entity_selector():
    with pytest.raises(MCSSyntaxError, match="Malformed entity selector"):
        tokenize("@a[type=pig")

def test_tokenizes_operators_and_punctuation():
    types = token_types("a + b == c && d || e ! f")
    assert types[0:3] == ["TT_NAME", "TT_BINARY_OPERATOR", "TT_NAME"]
    assert "TT_COMPARATOR" in types
    assert "TT_CONNECTOR" in types
    assert "TT_LOGICAL_NOT" in types
