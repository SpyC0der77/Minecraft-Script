from __future__ import annotations

from minecraft_script.errors import MCSSyntaxError
from minecraft_script.lexer.lexer import Lexer
from minecraft_script.lexer.tokens import Token
from minecraft_script.parser.nodes import MultilineCodeNode
from minecraft_script.parser.parser import Parser


def tokenize(code: str) -> tuple[Token, ...]:
    return Lexer(code).tokenize()


def parse_raw(code: str) -> MultilineCodeNode:
    lexer = Lexer(code + "\n")
    return Parser(lexer.tokenize()).parse()


def token_types(code: str) -> list[str]:
    return [token.tt_type for token in tokenize(code)]


def token_values(code: str) -> list[str]:
    return [token.value for token in tokenize(code)]


def expect_syntax_error(code: str, *, match: str | None = None) -> str:
    try:
        parse_raw(code)
    except (MCSSyntaxError, SyntaxError) as error:
        message = str(error)
        if match is not None and match not in message:
            raise AssertionError(f"Expected {match!r} in error message, got {message!r}") from error
        return message
    raise AssertionError(f"Expected syntax error for code: {code!r}")
