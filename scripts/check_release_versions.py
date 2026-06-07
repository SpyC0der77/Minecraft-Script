#!/usr/bin/env python3
"""Verify Python and npm release versions match before tagging or publishing."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise SystemExit("Could not find version in pyproject.toml")
    return match.group(1)


def read_npm_version() -> str:
    data = json.loads((ROOT / "npm" / "package.json").read_text(encoding="utf-8"))
    return data["version"]


def main() -> int:
    pyproject_version = read_pyproject_version()
    npm_version = read_npm_version()

    if pyproject_version != npm_version:
        print(
            "Version mismatch:\n"
            f"  pyproject.toml:   {pyproject_version}\n"
            f"  npm/package.json: {npm_version}",
            file=sys.stderr,
        )
        return 1

    print(f"Release versions aligned at {pyproject_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
