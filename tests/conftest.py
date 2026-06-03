from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import pytest

from minecraft_script.compiler import build_datapack
from minecraft_script.version_config import clear_version_context


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILD_TEST_ROOT = PROJECT_ROOT / "build_test"
UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CompiledDatapack:
    name: str
    root: Path

    @property
    def datapack_id(self) -> str:
        return self.name.lower().replace(" ", "_")

    @property
    def function_root(self) -> Path:
        return self.root / "data" / self.datapack_id / "function"

    def read_text(self, *parts: str) -> str:
        return self.root.joinpath(*parts).read_text(encoding="utf-8", errors="replace")

    def read_function(self, *parts: str) -> str:
        return self.function_root.joinpath(*parts).read_text(encoding="utf-8", errors="replace")

    def read_all_functions(self) -> str:
        return "\n".join(
            path.read_text(encoding="utf-8", errors="replace")
            for path in sorted(self.function_root.rglob("*.mcfunction"))
        )

    def has_function(self, *parts: str) -> bool:
        return self.function_root.joinpath(*parts).is_file()


def normalize_generated_content(content: str) -> str:
    return UUID_PATTERN.sub("<uuid>", content).replace("\\", "/")


@pytest.fixture
def compile_datapack():
    def _compile_datapack(source: str, datapack_name: str) -> CompiledDatapack:
        BUILD_TEST_ROOT.mkdir(exist_ok=True)
        datapack_root = BUILD_TEST_ROOT / datapack_name
        if datapack_root.exists():
            shutil.rmtree(datapack_root)

        try:
            build_datapack(source, datapack_name, str(BUILD_TEST_ROOT), verbose=False)
        finally:
            clear_version_context()
        return CompiledDatapack(datapack_name, datapack_root)

    return _compile_datapack


@pytest.fixture
def example_source():
    def _example_source(filename: str) -> str:
        return (PROJECT_ROOT / "examples" / filename).read_text(encoding="utf-8")

    return _example_source
