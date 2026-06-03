from pathlib import Path

from .. import parse_code
from .compiler import Compiler


def build_datapack(
    code: str,
    datapack_name: str,
    output_path: str,
    verbose: bool = False,
    *,
    source_path: str | Path | None = None,
    import_base_dir: str | Path | None = None,
) -> None:
    ast = parse_code(code, source_path=source_path, import_base_dir=import_base_dir)
    Compiler(ast, datapack_name, output_path, verbose).build()
