from .compile_types import *
from ..text_components import get_text_component_config, serialize_component
from ..version_config import get_version_context

function_output = tuple[tuple[str, ...], mcs_type]  # [commands, return value]


def _direct_tellraw_log_commands(args) -> tuple[str, ...]:
    version = get_version_context()
    config = get_text_component_config(version.orchestration)
    component = {"text": "", "extra": []}

    for index, arg in enumerate(args):
        if index > 0:
            component["extra"].append({"text": " "})

        nbt_component = {
            "storage": arg.get_storage(),
            "nbt": arg.get_nbt(),
        }
        if isinstance(arg, MCSTextComponent):
            nbt_component["interpret"] = True
        component["extra"].append(nbt_component)

    return (f"tellraw @a {serialize_component(component, config)}",)


def log(interpreter, args, context) -> function_output:
    version = get_version_context()
    log_style = version.orchestration.get("mcs_features", {}).get("log", {}).get("style")

    if log_style == "direct_tellraw":
        return _direct_tellraw_log_commands(args), MCSNull(context)

    max_length = 5
    commands: list[str] = []
    values: list[tuple[str, str]] = []

    for i in range(max_length):
        if i < len(args):
            values.append((args[i].get_storage(), args[i].get_nbt()))
        else:
            empty = MCSString(context)
            commands.append(empty.save_to_storage_cmd('""'))
            values.append((empty.get_storage(), empty.get_nbt()))

    storage_suffix = (
        " {"
        + ", ".join(f'"s{i}": "{values[i][0]}", "n{i}": "{values[i][1]}"' for i in range(max_length))
        + "}"
    )

    commands.append(version.render("builtin.log", storageSuffix=storage_suffix))

    return tuple(commands), MCSNull(context)


def command(interpreter, args, context) -> function_output:
    value = args[0]
    version = get_version_context()

    commands = tuple(version.render_lines(
        "builtin.command.setup",
        valueStorage=value.get_storage(),
        valueNbt=value.get_nbt(),
    ))

    return commands, MCSNull(context)


def get_block(interpreter, args, context) -> function_output:
    from .compile_interpreter import CompileContext
    x, y, z, *_ = args
    version = get_version_context()

    local_context = CompileContext(parent=context)
    mcs_obj = MCSString(context)

    interpreter.add_commands(
        local_context.mcfunction_name,
        version.render_lines(
            "builtin.get_block.body",
            resultStorage=mcs_obj.get_storage(),
            resultNbt=mcs_obj.get_nbt(),
        ),
    )

    setup_commands = tuple(version.render_lines(
        "builtin.get_block.setup",
        ctxStorage=f"mcs_{context.uuid}",
        xStorage=x.get_storage(),
        xNbt=x.get_nbt(),
        yStorage=y.get_storage(),
        yNbt=y.get_nbt(),
        zStorage=z.get_storage(),
        zNbt=z.get_nbt(),
        bodyPath=local_context.mcfunction_name,
    ))

    return setup_commands, mcs_obj


def set_block(interpreter, args, context) -> function_output:
    x, y, z, block_name, *_ = args
    version = get_version_context()

    commands = tuple(version.render_lines(
        "builtin.set_block.setup",
        ctxStorage=f"mcs_{context.uuid}",
        xStorage=x.get_storage(),
        xNbt=x.get_nbt(),
        yStorage=y.get_storage(),
        yNbt=y.get_nbt(),
        zStorage=z.get_storage(),
        zNbt=z.get_nbt(),
        blockStorage=block_name.get_storage(),
        blockNbt=block_name.get_nbt(),
    ))

    return commands, MCSNull(context)


def raycast_block(interpreter, args, context) -> function_output:
    from .compile_interpreter import CompileContext
    version = get_version_context()
    local_context = CompileContext(parent=context)
    raycast_id = generate_uuid()
    raycast_function: MCSFunction = args[0]
    raycast_range: mcs_type = args[1]
    raycast_loop_function: MCSFunction | None = args[2] if len(args) > 2 else None

    interpreter.schedule_function_generation(raycast_function)
    if raycast_loop_function is not None:
        interpreter.schedule_function_generation(raycast_loop_function)

    interpreter.add_commands(
        local_context.mcfunction_name,
        version.render_lines(
            "builtin.raycast_block.loop",
            raycastId=raycast_id,
            hitFunction=raycast_function.name,
            hasLoopFunction=raycast_loop_function is not None,
            loopFunction=raycast_loop_function.name if raycast_loop_function else "",
            loopPath=local_context.mcfunction_name,
        ),
    )

    setup_commands = (
        raycast_range.set_to_current_cmd(context),
        *version.render_lines(
            "builtin.raycast_block.setup",
            ctxStorage=f"mcs_{context.uuid}",
            rangeStorage=raycast_range.get_storage(),
            rangeNbt=raycast_range.get_nbt(),
            raycastId=raycast_id,
            loopPath=local_context.mcfunction_name,
        ),
    )

    return setup_commands, MCSNull(context)


def raycast_entity(interpreter, args, context) -> function_output:
    from .compile_interpreter import CompileContext
    version = get_version_context()
    local_context = CompileContext(parent=context)
    raycast_id = generate_uuid()
    raycast_function: MCSFunction = args[0]
    raycast_range: mcs_type = args[1]
    raycast_loop_function: MCSFunction | None = args[2] if len(args) > 2 else None

    interpreter.schedule_function_generation(raycast_function)
    if raycast_loop_function is not None:
        interpreter.schedule_function_generation(raycast_loop_function)

    interpreter.add_commands(
        local_context.mcfunction_name,
        version.render_lines(
            "builtin.raycast_entity.loop",
            raycastId=raycast_id,
            hitFunction=raycast_function.name,
            hasLoopFunction=raycast_loop_function is not None,
            loopFunction=raycast_loop_function.name if raycast_loop_function else "",
            loopPath=local_context.mcfunction_name,
        ),
    )

    setup_commands = (
        raycast_range.set_to_current_cmd(context),
        *version.render_lines(
            "builtin.raycast_entity.setup",
            ctxStorage=f"mcs_{context.uuid}",
            rangeStorage=raycast_range.get_storage(),
            rangeNbt=raycast_range.get_nbt(),
            raycastId=raycast_id,
            loopPath=local_context.mcfunction_name,
        ),
    )

    return setup_commands, MCSNull(context)


def give_item(interpreter, args, context) -> function_output:
    item: MCSString = args[0]
    components: MCSString = args[1] if len(args) > 1 else None
    count: MCSString = args[2] if len(args) > 2 else None
    version = get_version_context()

    params = {
        "ctxStorage": f"mcs_{context.uuid}",
        "itemStorage": item.get_storage(),
        "itemNbt": item.get_nbt(),
        "hasComponents": components is not None,
        "hasCount": count is not None,
    }
    if components is not None:
        params["componentsStorage"] = components.get_storage()
        params["componentsNbt"] = components.get_nbt()
    if count is not None:
        params["countStorage"] = count.get_storage()
        params["countNbt"] = count.get_nbt()

    commands = tuple(version.render_lines("builtin.give_item.setup", **params))
    return commands, MCSNull(context)


def concatenate(interpreter, args, context) -> function_output:
    from .compile_interpreter import CompileContext
    version = get_version_context()
    string_1: MCSString = args[0]
    string_2: MCSString = args[1]
    string_concat_context = CompileContext(parent=context)
    output_string = MCSString(context)

    interpreter.add_command(
        string_concat_context.mcfunction_name,
        version.render(
            "builtin.concatenate.macro",
            resultStorage=output_string.get_storage(),
            resultNbt=output_string.get_nbt(),
        ),
    )

    setup_commands = tuple(version.render_lines(
        "builtin.concatenate.setup",
        ctxStorage=f"mcs_{context.uuid}",
        s1Storage=string_1.get_storage(),
        s1Nbt=string_1.get_nbt(),
        s2Storage=string_2.get_storage(),
        s2Nbt=string_2.get_nbt(),
        macroPath=string_concat_context.mcfunction_name,
    ))

    return setup_commands, output_string


def append(interpreter, args, context) -> function_output:
    from .compile_interpreter import CompileContext
    version = get_version_context()
    list_arg: MCSList = args[0]
    value: mcs_type = args[1]
    set_key_context = CompileContext(parent=context)

    interpreter.add_command(
        set_key_context.mcfunction_name,
        version.render(
            "builtin.append.macro",
            listStorage=list_arg.get_storage(),
            listNbt=list_arg.get_nbt(),
            valueStorage=value.get_storage(),
            valueNbt=value.get_nbt(),
        ),
    )

    commands = tuple(version.render_lines(
        "builtin.append.setup",
        ctxStorage=f"mcs_{context.uuid}",
        listStorage=list_arg.get_storage(),
        listNbt=list_arg.get_nbt(),
        macroPath=set_key_context.mcfunction_name,
    ))

    return commands, MCSNull(context)


def mcs_range(interpreter, args, context) -> function_output:
    from .compile_interpreter import CompileContext
    version = get_version_context()
    range_bound: MCSNumber = args[0]
    result = MCSList(context)
    scoreboard_id = f"{generate_uuid()}"
    recursive_function = CompileContext(parent=context)
    set_index_function = CompileContext(parent=context)

    commands = (
        *version.render_lines(
            "builtin.range.init",
            scoreboardId=scoreboard_id,
            boundStorage=range_bound.get_storage(),
            boundNbt=range_bound.get_nbt(),
            resultStorage=result.get_storage(),
            resultNbt=result.get_nbt(),
            recursivePath=recursive_function.mcfunction_name,
        ),
        *version.render_lines(
            "builtin.range.cleanup",
            scoreboardId=scoreboard_id,
        ),
    )

    interpreter.add_commands(
        recursive_function.mcfunction_name,
        version.render_lines(
            "builtin.range.recursive",
            recursiveStorage=f"mcs_{recursive_function.uuid}",
            scoreboardId=scoreboard_id,
            setIndexPath=set_index_function.mcfunction_name,
            recursivePath=recursive_function.mcfunction_name,
        ),
    )

    interpreter.add_command(
        set_index_function.mcfunction_name,
        version.render(
            "builtin.range.set_index_macro",
            resultStorage=result.get_storage(),
            resultNbt=result.get_nbt(),
        ),
    )

    return commands, result


def give_clickable_item(interpreter, args, context) -> function_output:
    from .compile_interpreter import CompileContext
    version = get_version_context()
    click_function: MCSFunction = args[0]
    name: MCSString = args[1] if len(args) > 1 else None
    custom_model_data: MCSNumber = args[2] if len(args) > 2 else None

    interpreter.schedule_function_generation(click_function)

    click_function_id = interpreter.click_item_lookup.get(click_function.name)
    if click_function_id is None:
        click_function_id = (
            max(interpreter.click_item_lookup.values()) + 1
            if interpreter.click_item_lookup.values() else 0
        )
        interpreter.click_item_lookup[click_function.name] = click_function_id
        interpreter.add_command(
            f"clickable_items/{click_function_id}",
            version.render("click.register", userFunctionName=click_function.name),
        )

    if name is None:
        commands = (
            version.render("builtin.give_clickable.simple", clickId=click_function_id),
        )
    else:
        local_context = CompileContext(parent=context)
        params = {
            "ctxStorage": f"mcs_{context.uuid}",
            "nameStorage": name.get_storage(),
            "nameNbt": name.get_nbt(),
            "macroPath": local_context.mcfunction_name,
            "clickId": click_function_id,
            "hasCustomModel": custom_model_data is not None,
        }
        if custom_model_data is not None:
            params["modelStorage"] = custom_model_data.get_storage()
            params["modelNbt"] = custom_model_data.get_nbt()

        commands = tuple(version.render_lines("builtin.give_clickable.named_setup", **params))
        interpreter.add_command(
            local_context.mcfunction_name,
            version.render("builtin.give_clickable.named_macro", **params),
        )

    return commands, MCSNull(context)


builtin_functions = (
    log, command, concatenate,
    get_block, set_block,
    give_item, give_clickable_item,
    raycast_block, raycast_entity,
    append, mcs_range,
)
