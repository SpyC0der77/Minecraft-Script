from tests._helpers import normalize_generated_content


def test_scoreboard_event_example_compiles(compile_datapack, example_source):
    datapack = compile_datapack(
        example_source("scoreboard_event_test.mcs"),
        "Test Scoreboard Event",
    )

    assert (datapack.root / "pack.mcmeta").is_file()
    assert datapack.has_function("init.mcfunction")
    assert datapack.has_function("main.mcfunction")
    assert datapack.has_function("kill.mcfunction")
    assert datapack.has_function("user_functions", "hello.mcfunction")

    init_function = datapack.read_function("init.mcfunction")
    main_function = datapack.read_function("main.mcfunction")
    kill_function = datapack.read_function("kill.mcfunction")

    assert "scoreboard objectives add mcs_on_0 minecraft.mined:minecraft.diamond_ore" in init_function
    assert "execute as @a run scoreboard players set @s mcs_on_0 0" in init_function
    assert (
        "execute as @a at @s if score @s mcs_on_0 matches 1.. "
        "run function test_scoreboard_event:user_functions/hello"
    ) in main_function
    assert "execute as @a if score @s mcs_on_0 matches 1.. run scoreboard players set @s mcs_on_0 0" in main_function
    assert "scoreboard objectives remove mcs_on_0" in kill_function


def test_rich_text_example_compiles_tellraw_and_title_commands(compile_datapack, example_source):
    datapack = compile_datapack(
        example_source("tellraw_rich_text.mcs"),
        "Test Rich Text",
    )

    generated_functions = normalize_generated_content(datapack.read_all_functions())

    assert "tellraw @a" in generated_functions
    assert "title @a times" in generated_functions
    assert "title @a title" in generated_functions
    assert "title @a subtitle" in generated_functions
    assert "clickEvent" in generated_functions
    assert "hoverEvent" in generated_functions


def test_clickable_item_compile_generates_dispatch_functions(compile_datapack):
    source = """
function use_item() {
    command("say clicked");
}

function init() {
    @a give_clickable_item(use_item, "Hello Stick", 12);
}

function main() {
}
"""

    datapack = compile_datapack(source, "Test Clickable Item")

    assert datapack.has_function("clickable_items", "check.mcfunction")
    assert datapack.has_function("clickable_items", "run.mcfunction")
    assert datapack.has_function("clickable_items", "0.mcfunction")
    assert datapack.has_function("user_functions", "use_item.mcfunction")

    item_dispatch_function = datapack.read_function("clickable_items", "0.mcfunction")
    generated_functions = normalize_generated_content(datapack.read_all_functions())

    assert "function test_clickable_item:user_functions/use_item" in item_dispatch_function
    assert "minecraft:custom_data={mcs_click:0b}" in generated_functions
    assert "minecraft:custom_model_data=$(model)" in generated_functions
