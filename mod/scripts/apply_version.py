#!/usr/bin/env python3
"""Write mod/gradle.properties for a selected MCS profile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

MOD_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = MOD_ROOT / "versions" / "manifest.json"
GRADLE_PROPERTIES = MOD_ROOT / "gradle.properties"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", help="MCS profile key from versions/manifest.json")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    profile = manifest["profiles"].get(args.profile)
    if profile is None:
        known = ", ".join(manifest["profiles"].keys())
        raise SystemExit(f"Unknown profile {args.profile!r}. Known: {known}")

    lines = [
        "org.gradle.jvmargs=-Xmx4G",
        "org.gradle.parallel=true",
        "org.gradle.daemon=false",
        "",
        f"mcs_profile={args.profile}",
        f"minecraft_version={profile['minecraft_version']}",
        f"mcs_minecraft_profile={profile['mcs_profile']}",
        f"supported_game_versions={','.join(profile['supported_game_versions'])}",
        "",
        "architectury_plugin_version=3.4-SNAPSHOT",
        "architectury_loom_version=1.13-SNAPSHOT",
        "loom.ignoreDependencyLoomVersionValidation=true",
        "",
        "mod_version=0.1.0",
        "maven_group=dev.spyc0der77",
        "archives_base_name=mcs-packs",
        "mod_id=mcs_packs",
        "",
        f"fabric_loader_version={profile['fabric_loader_version']}",
        f"fabric_api_version={profile['fabric_api_version']}",
        f"forge_version={profile['forge_version']}",
        f"neoforge_version={profile['neoforge_version']}",
        f"architectury_api_version={profile['architectury_api_version']}",
        "",
        "enabled_platforms=fabric",
    ]
    GRADLE_PROPERTIES.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {GRADLE_PROPERTIES} for profile {args.profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
