from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


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
