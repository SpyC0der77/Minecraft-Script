from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"


@pytest.mark.parametrize(
    "example_file",
    sorted(EXAMPLES_DIR.glob("*.mcs")),
    ids=lambda path: path.name,
)
def test_example_compiles(compile_datapack, example_file: Path):
    datapack = compile_datapack(
        example_file.read_text(encoding="utf-8"),
        f"Test {example_file.stem.replace('_', ' ').title()}",
        source_path=example_file,
    )

    assert (datapack.root / "pack.mcmeta").is_file()
    assert datapack.has_function("main.mcfunction")
