from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .imports import parse_code_with_imports

_POSITION_PATTERN = re.compile(r"\(line (\d+), (\d+)\)")


@dataclass(frozen=True)
class Diagnostic:
    line: int
    column: int
    message: str
    severity: str = "error"

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


def diagnostic_from_exception(error: BaseException) -> Diagnostic:
    message = str(error)
    match = _POSITION_PATTERN.search(message)
    if match is not None:
        line = int(match.group(1))
        column = int(match.group(2))
    else:
        line = 1
        column = 0

    return Diagnostic(line=line, column=column, message=message)


def lint_code(
    code: str,
    *,
    source_path: str | Path | None = None,
    import_base_dir: str | Path | None = None,
) -> list[Diagnostic]:
    try:
        parse_code_with_imports(
            code,
            source_path=source_path,
            import_base_dir=import_base_dir,
        )
    except BaseException as error:
        return [diagnostic_from_exception(error)]

    return []
