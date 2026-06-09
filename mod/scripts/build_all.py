#!/usr/bin/env python3
"""Build MCS Packs mod artifacts for every MCS profile and loader."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

MOD_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = MOD_ROOT / "versions" / "manifest.json"
GRADLEW = MOD_ROOT / ("gradlew.bat" if sys.platform.startswith("win") else "gradlew")


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def run_build(profile: str, loader: str, skip_tests: bool) -> int:
    command = [str(GRADLEW), f":{loader}:build", f"-Pmcs_profile={profile}"]
    if skip_tests:
        command.append("-x")
        command.append("test")
    print(f"\n==> {' '.join(command)}", flush=True)
    return subprocess.run(command, cwd=MOD_ROOT, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", help="Build only this MCS profile key (e.g. 1.21.11)")
    parser.add_argument("--loader", choices=["fabric", "forge", "neoforge"], help="Build only this loader")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    if not GRADLEW.is_file():
        print(f"Gradle wrapper not found at {GRADLEW}. Run setup first.", file=sys.stderr)
        return 1

    manifest = load_manifest()
    profiles = [args.profile] if args.profile else list(manifest["profiles"].keys())
    loaders = [args.loader] if args.loader else manifest["loaders"]

    failures: list[str] = []
    for profile in profiles:
        if profile not in manifest["profiles"]:
            failures.append(f"unknown profile {profile!r}")
            continue
        for loader in loaders:
            code = run_build(profile, loader, args.skip_tests)
            if code != 0:
                failures.append(f"{profile}:{loader} (exit {code})")

    if failures:
        print("\nBuild failures:", file=sys.stderr)
        for item in failures:
            print(f"  - {item}", file=sys.stderr)
        return 1

    print("\nAll requested builds completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
