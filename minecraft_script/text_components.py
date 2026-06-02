import json
import re
from typing import Any


def get_text_component_config(orchestration: dict) -> dict:
    defaults = {
        "serialization": "json",
        "boolean_true": "true",
        "property_keys": {
            "text": "text",
            "extra": "extra",
            "color": "color",
            "bold": "bold",
            "italic": "italic",
            "underlined": "underlined",
            "strikethrough": "strikethrough",
            "obfuscated": "obfuscated",
            "font": "font",
            "insertion": "insertion",
            "translate": "translate",
            "with": "with",
            "click_event": "clickEvent",
            "hover_event": "hoverEvent",
            "action": "action",
            "value": "value",
            "command": "command",
            "url": "url",
            "open_url": "open_url",
            "run_command": "run_command",
            "suggest_command": "suggest_command",
            "copy_to_clipboard": "copy_to_clipboard",
            "show_text": "show_text",
            "show_item": "show_item",
            "id": "id",
            "count": "count",
            "interpret": "interpret",
            "storage": "storage",
            "nbt": "nbt",
        },
        "commands": {
            "tellraw": "tellraw {{target}} {{component}}",
            "title": "title {{target}} {{mode}} {{component}}",
            "title_times": "title {{target}} times {{fadeIn}} {{stay}} {{fadeOut}}",
        },
    }
    configured = orchestration.get("mcs_features", {}).get("text_component", {})
    merged = {**defaults, **configured}
    merged["property_keys"] = {**defaults["property_keys"], **configured.get("property_keys", {})}
    merged["commands"] = {**defaults["commands"], **configured.get("commands", {})}
    return merged


def _map_keys(value: Any, keys: dict[str, str]) -> Any:
    if isinstance(value, list):
        return [_map_keys(item, keys) for item in value]
    if not isinstance(value, dict):
        return value

    mapped: dict[str, Any] = {}
    for key, item in value.items():
        mapped[keys.get(key, key)] = _map_keys(item, keys)
    return mapped


def _escape_snbt_string(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _serialize_snbt_value(value: Any, keys: dict[str, str], boolean_true: str) -> str:
    if isinstance(value, bool):
        return boolean_true if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        if re.fullmatch(r"[#a-z0-9_]+", value):
            return value
        return _escape_snbt_string(value)
    if isinstance(value, list):
        inner = ", ".join(_serialize_snbt_value(item, keys, boolean_true) for item in value)
        return f"[{inner}]"
    if isinstance(value, dict):
        parts: list[str] = []
        for key, item in value.items():
            serialized_key = keys.get(key, key)
            parts.append(f"{serialized_key}: {_serialize_snbt_value(item, keys, boolean_true)}")
        return "{" + ", ".join(parts) + "}"
    raise TypeError(f"Unsupported text component value type: {type(value)!r}")


def serialize_component(component: dict, config: dict) -> str:
    keys = config["property_keys"]
    mapped = _map_keys(component, keys)
    if config["serialization"] == "snbt":
        return _serialize_snbt_value(mapped, keys, config["boolean_true"])
    return json.dumps(mapped, ensure_ascii=False, separators=(",", ":"))


def component_from_nbt_reference(storage: str, nbt: str, *, interpret: bool = True) -> dict:
    return {
        "storage": storage,
        "nbt": nbt,
        "interpret": interpret,
    }
