import pytest


def test_scoreboard_event_function_cannot_have_parameters(compile_datapack):
    source = """
function bad_event(player) on "minecraft.mined:minecraft.diamond_ore" {
    log(player);
}
"""

    with pytest.raises(ValueError, match="cannot have parameters"):
        compile_datapack(source, "Test Event Parameters Error")


def test_scoreboard_event_criteria_must_be_command_safe(compile_datapack):
    source = """
function bad_event() on "minecraft.mined:minecraft.diamond ore" {
    log("invalid criteria");
}
"""

    with pytest.raises(ValueError, match="Invalid scoreboard criteria"):
        compile_datapack(source, "Test Event Criteria Error")
