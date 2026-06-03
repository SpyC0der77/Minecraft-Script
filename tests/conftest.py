from __future__ import annotations

import shutil

import pytest

from minecraft_script.compiler import build_datapack
from minecraft_script.version_config import clear_version_context
from tests._helpers import BUILD_TEST_ROOT, PROJECT_ROOT, CompiledDatapack


@pytest.fixture
def compile_datapack():
    compiled_roots = []

    def _compile_datapack(source: str, datapack_name: str) -> CompiledDatapack:
        BUILD_TEST_ROOT.mkdir(exist_ok=True)
        datapack_root = BUILD_TEST_ROOT / datapack_name
        compiled_roots.append(datapack_root)
        if datapack_root.exists():
            shutil.rmtree(datapack_root)

        try:
            build_datapack(source, datapack_name, str(BUILD_TEST_ROOT), verbose=False)
        finally:
            clear_version_context()
        return CompiledDatapack(datapack_name, datapack_root)

    yield _compile_datapack

    clear_version_context()
    for datapack_root in reversed(compiled_roots):
        if datapack_root.exists():
            shutil.rmtree(datapack_root)
    if BUILD_TEST_ROOT.exists() and not any(BUILD_TEST_ROOT.iterdir()):
        BUILD_TEST_ROOT.rmdir()


@pytest.fixture
def example_source():
    def _example_source(filename: str) -> str:
        return (PROJECT_ROOT / "examples" / filename).read_text(encoding="utf-8")

    return _example_source
