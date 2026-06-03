from __future__ import annotations

from pathlib import Path

from .errors import MCSImportError
from .lexer.lexer import Lexer
from .parser.nodes import ImportNode, MultilineCodeNode
from .parser.parser import Parser


def parse_code_with_imports(
    code: str,
    *,
    source_path: str | Path | None = None,
    import_base_dir: str | Path | None = None,
):
    ast = _parse_raw(code)
    if source_path is None and import_base_dir is None:
        return _resolve_imports(ast, None, None, [])

    resolved_source_path = Path(source_path).resolve() if source_path is not None else None
    resolved_base_dir = Path(import_base_dir).resolve() if import_base_dir is not None else None
    if resolved_base_dir is None and resolved_source_path is not None:
        resolved_base_dir = resolved_source_path.parent

    stack = [resolved_source_path] if resolved_source_path is not None else []
    return _resolve_imports(ast, resolved_source_path, resolved_base_dir, stack)


def _parse_raw(code: str):
    lexer = Lexer(code + "\n")
    parser = Parser(lexer.tokenize())
    return parser.parse()


def _resolve_imports(
    node,
    source_path: Path | None,
    import_base_dir: Path | None,
    stack: list[Path],
):
    if not isinstance(node, MultilineCodeNode):
        return node

    resolved_nodes = []
    for statement in node.get_nodes():
        if not isinstance(statement, ImportNode):
            resolved_nodes.append(statement)
            continue

        imported_path = _resolve_import_path(statement.get_path(), source_path, import_base_dir)
        imported_body = _load_imported_body(imported_path, stack)

        if statement.get_alias() is None:
            resolved_nodes.extend(imported_body.get_nodes())
        else:
            resolved_nodes.append(statement.with_body(imported_body))

    return MultilineCodeNode(tuple(resolved_nodes), node.get_position())


def _resolve_import_path(import_path: str, source_path: Path | None, import_base_dir: Path | None) -> Path:
    path = Path(import_path)
    if path.is_absolute():
        return path.resolve()

    base_dir = source_path.parent if source_path is not None else import_base_dir
    if base_dir is None:
        raise MCSImportError(
            f"Cannot resolve relative import {import_path!r} without source_path or import_base_dir"
        )
    return (base_dir / path).resolve()


def _load_imported_body(imported_path: Path, stack: list[Path]):
    if not imported_path.is_file():
        raise MCSImportError(f"Could not find import file {str(imported_path)!r}")

    if imported_path in stack:
        cycle = " -> ".join(str(path) for path in (*stack, imported_path))
        raise MCSImportError(f"Circular import detected: {cycle}")

    code = imported_path.read_text(encoding="utf-8")
    ast = _parse_raw(code)
    return _resolve_imports(ast, imported_path, imported_path.parent, [*stack, imported_path])
