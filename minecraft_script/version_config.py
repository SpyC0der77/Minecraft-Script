import json
import os
from pathlib import Path

from pybars import Compiler

from .common import COMMON_CONFIG, module_folder

_handlebars = Compiler()
_version_ctx: "VersionContext | None" = None
_profile_cache: dict[str, dict] = {}


def get_minecraft_version() -> str:
    return COMMON_CONFIG["minecraft_version"]


def load_version_profile(version: str | None = None) -> dict:
    version = version or get_minecraft_version()
    if version in _profile_cache:
        return _profile_cache[version]

    profile_path = Path(module_folder) / "versions" / f"{version}.json"
    if not profile_path.is_file():
        supported = list_supported_versions()
        raise FileNotFoundError(
            f"Unknown minecraft version {version!r}. "
            f"Expected profile at {profile_path}. "
            f"Supported: {', '.join(supported) or '(none)'}"
        )

    with profile_path.open("rt", encoding="utf-8") as file:
        profile = json.load(file)

    _profile_cache[version] = profile
    return profile


def list_supported_versions() -> list[str]:
    versions_dir = Path(module_folder) / "versions"
    if not versions_dir.is_dir():
        return []
    return sorted(
        path.stem
        for path in versions_dir.glob("*.json")
        if path.name != "index.json"
    )


def predefined_root(category: str, version: str | None = None) -> str:
    version = version or get_minecraft_version()
    return str(Path(module_folder) / "compiler" / "build_templates" / category / version)


class VersionRenderer:
    def __init__(self, profile: dict):
        self.profile = profile
        self._compiled: dict[str, object] = {}

    def render(self, key: str, **params) -> str:
        templates = self.profile.get("templates")
        if templates is None or key not in templates:
            raise KeyError(
                f"Template {key!r} not defined for Minecraft {self.profile.get('minecraft_version')!r}"
            )
        if key not in self._compiled:
            self._compiled[key] = _handlebars.compile(templates[key])
        result = self._compiled[key](params)
        return result.strip() if isinstance(result, str) else str(result).strip()

    def render_lines(self, key: str, **params) -> list[str]:
        text = self.render(key, **params)
        return text.split("\n") if text else []


class VersionContext:
    def __init__(self, datapack_id: str, profile: dict | None = None):
        self.datapack_id = datapack_id
        self.profile = profile or load_version_profile()
        self.renderer = VersionRenderer(self.profile)
        self.function_dir = self.profile["paths"]["function_dir"]
        self.function_tag_dir = self.profile["paths"]["function_tag_dir"]
        self.pack_format = str(self.profile["pack_format"])

    def _params(self, **params) -> dict:
        merged = dict(self.profile.get("constants", {}))
        merged.setdefault("datapack_id", self.datapack_id)
        merged.update(params)
        return merged

    def render(self, key: str, **params) -> str:
        return self.renderer.render(key, **self._params(**params))

    def render_lines(self, key: str, **params) -> list[str]:
        return self.renderer.render_lines(key, **self._params(**params))


def init_version_context(datapack_id: str) -> VersionContext:
    global _version_ctx
    _version_ctx = VersionContext(datapack_id)
    return _version_ctx


def get_version_context() -> VersionContext:
    if _version_ctx is None:
        raise RuntimeError("Version context not initialized. Call init_version_context first.")
    return _version_ctx


def clear_version_context() -> None:
    global _version_ctx
    _version_ctx = None
