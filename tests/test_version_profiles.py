import json
from pathlib import Path

from minecraft_script.common import COMMON_CONFIG
from minecraft_script.text_components import get_text_component_config, serialize_component
from minecraft_script.version_config import VersionContext, list_supported_versions, load_version_profile

VERSIONS_DIR = Path(__file__).resolve().parents[1] / "minecraft_script" / "versions"


NEW_SUPPORTED_VERSIONS = {
    "1.21.4",
    "1.21.5",
    "1.21.6",
    "1.21.7",
    "1.21.8",
    "1.21.9",
    "1.21.10",
    "1.21.11",
    "26.1",
}


def test_new_version_profiles_are_supported():
    assert NEW_SUPPORTED_VERSIONS.issubset(set(list_supported_versions()))


def test_equivalent_version_profiles_use_range_files():
    index = json.loads((VERSIONS_DIR / "index.json").read_text(encoding="utf-8"))

    assert (VERSIONS_DIR / "1.21.7-8.json").is_file()
    assert (VERSIONS_DIR / "1.21.9-10.json").is_file()
    assert not (VERSIONS_DIR / "1.21.7.json").exists()
    assert not (VERSIONS_DIR / "1.21.8.json").exists()
    assert not (VERSIONS_DIR / "1.21.9.json").exists()
    assert not (VERSIONS_DIR / "1.21.10.json").exists()

    assert index["profiles"]["1.21.8"] == "1.21.7-8"
    assert index["profiles"]["1.21.10"] == "1.21.9-10"
    assert load_version_profile("1.21.8")["minecraft_version"] == "1.21.7-8"
    assert load_version_profile("1.21.10")["minecraft_version"] == "1.21.9-10"


def test_legacy_and_range_pack_metadata_render_for_new_profiles():
    legacy_context = VersionContext("test_pack", load_version_profile("1.21.5"))
    legacy_pack = json.loads(legacy_context.render_pack_mcmeta())["pack"]

    assert legacy_pack["pack_format"] == 71
    assert legacy_pack["supported_formats"] == [71, 71]

    range_context = VersionContext("test_pack", load_version_profile("1.21.11"))
    range_pack = json.loads(range_context.render_pack_mcmeta())["pack"]

    assert "pack_format" not in range_pack
    assert "supported_formats" not in range_pack
    assert range_pack["min_format"] == [94, 1]
    assert range_pack["max_format"] == [94, 1]


def test_range_profiles_do_not_keep_legacy_pack_mcmeta_template():
    for version in ("1.21.9", "1.21.11", "26.1"):
        profile = load_version_profile(version)
        assert profile["orchestration"]["pack"]["format"]["style"] == "range"
        assert profile["templates"]["pack.mcmeta"] == profile["templates"]["pack.mcmeta.range"]
        assert "pack_format" not in profile["templates"]["pack.mcmeta"]
        assert "supported_formats" not in profile["templates"]["pack.mcmeta"]


def test_1215_profile_uses_snbt_text_components_and_new_item_component_shapes():
    context = VersionContext("test_pack", load_version_profile("1.21.5"))
    text_config = get_text_component_config(context.orchestration)

    component = serialize_component({"text": "Hello"}, text_config)
    clickable = context.render(
        "builtin.give_clickable.named_macro",
        clickId=3,
        hasCustomModel=True,
    )

    assert component == "{text: \"Hello\"}"
    assert "minecraft:custom_name={text:\"$(name)\"}" in clickable
    assert "minecraft:custom_model_data={floats:[$(model)]}" in clickable


def test_1215_compile_outputs_snbt_text_components(monkeypatch, compile_datapack):
    monkeypatch.setitem(COMMON_CONFIG, "minecraft_version", "1.21.5")

    datapack = compile_datapack(
        """
function init() {
    tellraw("@a", text().text("Run").click_run("/say hi"));
}

function main() {
}
""",
        "Test 1215 Text",
    )

    generated_functions = datapack.read_all_functions()

    assert "tellraw @a {text: \"Run\", click_event: {action: run_command, command: \"/say hi\"}}" in generated_functions
    assert "clickEvent" not in generated_functions


def test_1219_compile_outputs_range_pack_metadata(monkeypatch, compile_datapack):
    monkeypatch.setitem(COMMON_CONFIG, "minecraft_version", "1.21.9")

    datapack = compile_datapack(
        """
function init() {
    command("# init");
}

function main() {
    command("# main");
}
""",
        "Test 1219 Pack",
    )

    pack = json.loads(datapack.read_text("pack.mcmeta"))["pack"]

    assert pack["min_format"] == [88, 0]
    assert pack["max_format"] == [88, 0]
    assert "pack_format" not in pack
    assert "supported_formats" not in pack
