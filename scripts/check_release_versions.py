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
    project_section = re.search(
        r"^\[project\]\s*\n(.*?)(?=^\[|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not project_section:
        raise SystemExit("Could not find [project] section in pyproject.toml")

    match = re.search(
        r'^version\s*=\s*"([^"]+)"',
        project_section.group(1),
        re.MULTILINE,
    )
    if not match:
        raise SystemExit('Could not find version in pyproject.toml [project] section')
    return match.group(1)


def read_npm_version() -> str:
    data = json.loads((ROOT / "npm" / "package.json").read_text(encoding="utf-8"))
    return data["version"]


def normalize_tag_version(tag: str) -> str:
    if not tag.startswith("v"):
        raise SystemExit(f"Release tag must start with 'v', got {tag!r}")
    return tag[1:]


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    tag = None
    if "--tag" in args:
        index = args.index("--tag")
        try:
            tag = args[index + 1]
        except IndexError:
            raise SystemExit("Missing value for --tag") from None
        del args[index:index + 2]

    if args:
        raise SystemExit(f"Unknown arguments: {' '.join(args)}")

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

    if tag is not None:
        tag_version = normalize_tag_version(tag)
        if tag_version != pyproject_version:
            print(
                "Tag version mismatch:\n"
                f"  git tag:          {tag_version}\n"
                f"  pyproject.toml:   {pyproject_version}\n"
                f"  npm/package.json: {npm_version}",
                file=sys.stderr,
            )
            return 1

    print(f"Release versions aligned at {pyproject_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
