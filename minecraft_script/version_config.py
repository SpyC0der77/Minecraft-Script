import json
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


def resolve_orchestration(profile: dict) -> dict:
    """Normalize orchestration settings (with legacy top-level fallbacks)."""
    orchestration = dict(profile.get("orchestration", {}))
    legacy_paths = profile.get("paths", {})
    legacy_constants = profile.get("constants", {})

    paths = {
        "function_dir": "functions",
        "function_tag_dir": "functions",
        "namespace_tags_dir": "tags",
        "block_tag_category": "block",
        "user_functions": "user_functions",
        "code_blocks": "code_blocks",
        "clickable_items": "clickable_items",
        "builtins": "builtins",
        "math": "math",
        **orchestration.get("paths", {}),
        **legacy_paths,
    }

    pack_section = orchestration.get("pack", {})
    pack_format_section = pack_section.get("format", {})
    pack_format = (
        pack_format_section.get("pack_format")
        or profile.get("pack_format")
        or 41
    )

    pack = {
        "description": pack_section.get(
            "description",
            "This datapack was generated using Minecraft-Script",
        ),
        "format": {
            "style": pack_format_section.get("style", "legacy"),
            "pack_format": pack_format,
            "major": pack_format_section.get("major"),
            "minor": pack_format_section.get("minor"),
            "min_major": pack_format_section.get("min_major"),
            "min_minor": pack_format_section.get("min_minor"),
            "max_major": pack_format_section.get("max_major"),
            "max_minor": pack_format_section.get("max_minor"),
        },
    }

    function_tags = {
        "tick": {"file": "tick.json", "entry": "main"},
        "load": {"file": "load.json", "entry": "init"},
        **orchestration.get("function_tags", {}),
    }

    mcs_features = orchestration.get("mcs_features", {})
    click = {
        "scoreboard_criterion": "minecraft.used:minecraft.carrot_on_a_stick",
        "selected_item_path": "SelectedItem.tag.mcs_click",
        **mcs_features.get("click", {}),
    }
    if "clickScoreboardCriterion" in legacy_constants:
        click["scoreboard_criterion"] = legacy_constants["clickScoreboardCriterion"]
    if "clickSelectedItemPath" in legacy_constants:
        click["selected_item_path"] = legacy_constants["clickSelectedItemPath"]

    clickable_item = {
        "item_id": "carrot_on_a_stick",
        **mcs_features.get("clickable_item", {}),
    }
    if "clickItemId" in legacy_constants:
        clickable_item["item_id"] = legacy_constants["clickItemId"]

    get_block = {
        "entity_loot_result_path": "equipment.head.id",
        **mcs_features.get("get_block", {}),
    }
    if "getBlockEntityPath" in legacy_constants:
        get_block["entity_loot_result_path"] = legacy_constants["getBlockEntityPath"]

    return {
        "paths": paths,
        "pack": pack,
        "function_tags": function_tags,
        "scoreboards": {
            "math": "mcs_math",
            "click": "mcs_click",
            **orchestration.get("scoreboards", {}),
        },
        "storage": {
            "click": "mcs_click",
            **orchestration.get("storage", {}),
        },
        "mcs_features": {
            "click": click,
            "clickable_item": clickable_item,
            "get_block": get_block,
        },
        "datapack_lifecycle": orchestration.get(
            "datapack_lifecycle",
            {"disable_target": "file"},
        ),
    }


def orchestration_template_params(orchestration: dict) -> dict:
    """Handlebars params derived from orchestration (not user NBT in .mcs source)."""
    pack_format = orchestration["pack"]["format"]
    click = orchestration["mcs_features"]["click"]
    clickable_item = orchestration["mcs_features"]["clickable_item"]
    get_block = orchestration["mcs_features"]["get_block"]

    params = {
        "pack_format": pack_format["pack_format"],
        "packDescription": orchestration["pack"]["description"],
        "formatMajor": pack_format.get("major", pack_format["pack_format"]),
        "formatMinor": pack_format.get("minor", 0),
        "formatMinMajor": pack_format.get("min_major", pack_format.get("major")),
        "formatMinMinor": pack_format.get("min_minor", 0),
        "formatMaxMajor": pack_format.get("max_major", pack_format.get("major")),
        "formatMaxMinor": pack_format.get("max_minor", 0),
        "clickScoreboardCriterion": click["scoreboard_criterion"],
        "clickSelectedItemPath": click["selected_item_path"],
        "clickItemId": clickable_item["item_id"],
        "getBlockEntityPath": get_block["entity_loot_result_path"],
    }
    return params


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
        self.orchestration = resolve_orchestration(self.profile)
        self.renderer = VersionRenderer(self.profile)
        self.paths = self.orchestration["paths"]
        self.function_dir = self.paths["function_dir"]
        self.function_tag_dir = self.paths["function_tag_dir"]
        self.pack_format = str(self.orchestration["pack"]["format"]["pack_format"])

    def _params(self, **params) -> dict:
        merged = orchestration_template_params(self.orchestration)
        merged.setdefault("datapack_id", self.datapack_id)
        merged.update(params)
        return merged

    def render(self, key: str, **params) -> str:
        return self.renderer.render(key, **self._params(**params))

    def render_lines(self, key: str, **params) -> list[str]:
        return self.renderer.render_lines(key, **self._params(**params))

    def render_pack_mcmeta(self) -> str:
        style = self.orchestration["pack"]["format"].get("style", "legacy")
        if style == "range":
            return self.render("pack.mcmeta.range")
        return self.render("pack.mcmeta")

    def render_function_tag(self, tag_key: str) -> str:
        tag = self.orchestration["function_tags"][tag_key]
        return self.render(
            f"function_tags.{tag_key}",
            tagEntry=tag["entry"],
        )

    def function_tag_path(self, tag_key: str) -> str:
        return self.orchestration["function_tags"][tag_key]["file"]


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
