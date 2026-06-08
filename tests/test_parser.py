import pytest

from minecraft_script.errors import MCSParserError, MCSSyntaxError
from minecraft_script.parser.nodes import (
    AsyncWhileLoopNode,
    BinaryOperationNode,
    DefineFunctionNode,
    EntitySelectorNode,
    ForLoopNode,
    FunctionCallNode,
    IfConditionNode,
    ImportNode,
    ListNode,
    MultilineCodeNode,
    NumberNode,
    StringNode,
    VariableAccessNode,
    VariableDeclareNode,
    WhileLoopNode,
)
from tests._parse_helpers import expect_syntax_error, parse_raw


def get_statements(code: str):
    ast = parse_raw(code)
    assert isinstance(ast, MultilineCodeNode)
    return ast.get_nodes()


def test_parses_variable_declaration_and_assignment():
    declare, assign = get_statements('var count = 0; set count = count + 1;')

    assert isinstance(declare, VariableDeclareNode)
    assert declare.get_name() == "count"
    assert isinstance(declare.get_value(), NumberNode)

    assert assign.get_name() == "count"
    assert isinstance(assign.get_value(), BinaryOperationNode)


def test_parses_function_definition_and_call():
    define, call = get_statements(
        'function greet(name) { return name; }\n'
        'greet("world");'
    )

    assert isinstance(define, DefineFunctionNode)
    assert define.get_name() == "greet"
    assert define.get_parameter_names() == ["name"]

    assert isinstance(call, FunctionCallNode)
    assert call.get_root().get_name() == "greet"
    assert len(call.get_arguments()) == 1
    assert isinstance(call.get_arguments()[0], StringNode)


def test_parses_if_else_conditionals():
    node = get_statements('if (true) { log("yes"); } else { log("no"); }')[0]
    assert isinstance(node, IfConditionNode)


def test_parses_while_and_async_while_loops():
    while_node = get_statements('while (i < 5) { set i = i + 1; }')[0]
    assert isinstance(while_node, WhileLoopNode)

    async_node = get_statements('async while (running) { tick(); }')[0]
    assert isinstance(async_node, AsyncWhileLoopNode)


def test_parses_for_loop_over_range():
    node = get_statements('for (item in range(3)) { log(item); }')[0]
    assert isinstance(node, ForLoopNode)
    assert node.get_child_name() == "item"
    assert isinstance(node.get_iterable(), FunctionCallNode)


def test_parses_import_statements():
    inline, aliased = get_statements(
        'import "./helpers.mcs";\n'
        'import "./utils.mcs" as utils;'
    )

    assert isinstance(inline, ImportNode)
    assert inline.get_path() == "./helpers.mcs"
    assert inline.get_alias() is None

    assert isinstance(aliased, ImportNode)
    assert aliased.get_path() == "./utils.mcs"
    assert aliased.get_alias() == "utils"


def test_parses_entity_selector_statement():
    node = get_statements('@a[tag=vip] log("hello");')[0]
    assert isinstance(node, EntitySelectorNode)
    assert node.get_selector() == '@a[tag=vip]'
    assert isinstance(node.get_statement(), FunctionCallNode)


def test_parses_list_literals():
    node = get_statements('var items = [1, "two", true];')[0]
    value = node.get_value()
    assert isinstance(value, ListNode)
    assert len(value.get_node_list()) == 3


def test_parses_attribute_access_and_chaining():
    node = get_statements('var msg = text("Hi").color("gold").bold();')[0]
    value = node.get_value()
    assert isinstance(value, FunctionCallNode)
    assert value.get_root().get_name() == "bold"


def test_raises_for_missing_statement_semicolon():
    with pytest.raises(MCSSyntaxError, match="Unexpected end of statement"):
        parse_raw('var x = 1\nvar y = 2;')


def test_raises_for_unclosed_parenthesis():
    with pytest.raises(MCSSyntaxError, match="Expected '\\)'"):
        parse_raw('if (true { log("x"); }')


def test_raises_for_invalid_async_usage():
    expect_syntax_error('async for (x in range(2)) { log(x); }', match='Invalid use of "async"')


def test_raises_for_unknown_token_in_expression():
    with pytest.raises(MCSParserError, match="Unknown token"):
        parse_raw('var x = import;')
