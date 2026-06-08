def test_unused_user_functions_are_not_generated(compile_datapack):
    source = """
function used() {
    log("hello");
}

function unused() {
    log("never called");
}

function init() {
    used();
}

function main() {
}
"""

    datapack = compile_datapack(source, "Test Tree Shake Unused")

    assert datapack.has_function("user_functions", "used.mcfunction")
    assert datapack.has_function("user_functions", "init.mcfunction")
    assert not datapack.has_function("user_functions", "unused.mcfunction")


def test_transitive_reachability_keeps_called_helpers(compile_datapack):
    source = """
function helper() {
    log("helper");
}

function entry() {
    helper();
}

function init() {
    entry();
}

function main() {
}
"""

    datapack = compile_datapack(source, "Test Tree Shake Transitive")

    assert datapack.has_function("user_functions", "entry.mcfunction")
    assert datapack.has_function("user_functions", "helper.mcfunction")


def test_scoreboard_event_functions_are_always_generated(compile_datapack):
    source = """
function reward_miner() on "minecraft.mined:minecraft.diamond_ore" {
    log("reward");
}

function unused_helper() {
    log("unused");
}

function init() {
    command("# tree shake event init");
}

function main() {
    command("# tree shake event main");
}
"""

    datapack = compile_datapack(source, "Test Tree Shake Event")

    assert datapack.has_function("user_functions", "reward_miner.mcfunction")
    assert not datapack.has_function("user_functions", "unused_helper.mcfunction")


def test_click_handler_functions_are_generated_when_referenced(compile_datapack):
    source = """
function use_item() {
    command("say clicked");
}

function unused_click_handler() {
    command("say unused");
}

function init() {
    @a give_clickable_item(use_item, "Hello Stick", 12);
}

function main() {
}
"""

    datapack = compile_datapack(source, "Test Tree Shake Click")

    assert datapack.has_function("user_functions", "use_item.mcfunction")
    assert datapack.has_function("clickable_items", "0.mcfunction")
    assert not datapack.has_function("user_functions", "unused_click_handler.mcfunction")
