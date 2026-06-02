from copy import deepcopy

from ..errors import MCSTypeError, MCSValueError
from ..text_components import (
    component_from_nbt_reference,
    get_text_component_config,
    serialize_component,
)
from ..version_config import get_version_context
from .compile_types import MCSFunction, MCSNull, MCSNumber, MCSString, MCSTextComponent, MCSVariable, mcs_type

function_output = tuple[tuple[str, ...], mcs_type]

_TITLE_MODES = frozenset({"title", "subtitle", "actionbar"})


def _require_string_arg(args: tuple[mcs_type, ...], method_name: str) -> MCSString:
    if len(args) != 1:
        raise MCSTypeError(f"TextComponent.{method_name}() takes 1 argument, got {len(args)}")
    arg = args[0]
    if not isinstance(arg, MCSString):
        raise MCSTypeError(
            f"TextComponent.{method_name}() expects a string, got {arg.class_name()!r}"
        )
    return arg


def _require_text_component_arg(args: tuple[mcs_type, ...], method_name: str) -> MCSTextComponent:
    if len(args) != 1:
        raise MCSTypeError(f"TextComponent.{method_name}() takes 1 argument, got {len(args)}")
    arg = args[0]
    if not isinstance(arg, MCSTextComponent):
        raise MCSTypeError(
            f"TextComponent.{method_name}() expects a TextComponent, got {arg.class_name()!r}"
        )
    return arg


def _literal_string_value(string_arg: MCSString) -> str | None:
    literal = getattr(string_arg, "literal_value", None)
    if isinstance(literal, str):
        return literal

    save_cmd = string_arg.save_to_storage_cmd("")
    marker = "set value "
    if marker not in save_cmd:
        return None
    stored = save_cmd.rsplit(marker, maxsplit=1)[-1]
    if not (stored.startswith('"') and stored.endswith('"')):
        return None
    return stored[1:-1]


def _require_literal_string(string_arg: MCSString, context: str) -> str:
    literal = _literal_string_value(string_arg)
    if literal is None:
        raise MCSValueError(f"{context} must be a string literal at compile time")
    return literal


def _literal_number_value(number_arg: MCSNumber) -> int | None:
    literal = getattr(number_arg, "literal_value", None)
    if isinstance(literal, int):
        return literal

    save_cmd = number_arg.save_to_storage_cmd("0")
    marker = "set value "
    if marker not in save_cmd:
        return None
    stored = save_cmd.rsplit(marker, maxsplit=1)[-1]
    if not stored.isdigit():
        return None
    return int(stored)


def _text_component_from_string(string_arg: MCSString) -> dict:
    literal = _literal_string_value(string_arg)
    if literal is not None:
        return {"text": literal}
    return component_from_nbt_reference(
        string_arg.get_storage(),
        string_arg.get_nbt(),
        interpret=True,
    )


def _bind_method(receiver: MCSTextComponent, method_name: str, handler):
    def call(_interpreter, args, context) -> function_output:
        return (), handler(receiver, args, context)

    bound = MCSFunction(f"TextComponent.{method_name}", None, None, receiver.context)
    bound.call = call
    return bound


def _method_text(receiver: MCSTextComponent, args, context) -> MCSTextComponent:
    string_arg = _require_string_arg(args, "text")
    result = receiver.clone()
    result.component = _text_component_from_string(string_arg)
    return result


def _method_color(receiver: MCSTextComponent, args, context) -> MCSTextComponent:
    string_arg = _require_string_arg(args, "color")
    result = receiver.clone()
    result.component["color"] = _require_literal_string(string_arg, "TextComponent.color()")
    return result


def _method_font(receiver: MCSTextComponent, args, context) -> MCSTextComponent:
    string_arg = _require_string_arg(args, "font")
    result = receiver.clone()
    result.component["font"] = _require_literal_string(string_arg, "TextComponent.font()")
    return result


def _method_insertion(receiver: MCSTextComponent, args, context) -> MCSTextComponent:
    string_arg = _require_string_arg(args, "insertion")
    result = receiver.clone()
    result.component["insertion"] = _require_literal_string(string_arg, "TextComponent.insertion()")
    return result


def _method_formatting_flag(receiver: MCSTextComponent, args, flag_name: str) -> MCSTextComponent:
    if len(args) != 0:
        raise MCSTypeError(f"TextComponent.{flag_name}() takes 0 arguments, got {len(args)}")
    result = receiver.clone()
    result.component[flag_name] = True
    return result


def _method_translate(receiver: MCSTextComponent, args, context) -> MCSTextComponent:
    if len(args) != 1:
        raise MCSTypeError(f"TextComponent.translate() takes 1 argument, got {len(args)}")

    key_arg = args[0]
    if not isinstance(key_arg, MCSString):
        raise MCSTypeError(
            f"TextComponent.translate() expects a string key, got {key_arg.class_name()!r}"
        )

    result = receiver.clone()
    result.component = {
        "translate": _require_literal_string(key_arg, "TextComponent.translate()"),
    }
    return result


def _method_append(receiver: MCSTextComponent, args, context) -> MCSTextComponent:
    other = _require_text_component_arg(args, "append")
    result = receiver.clone()
    if not result.component:
        return other.clone()

    extra = list(result.component.get("extra", []))
    extra.append(deepcopy(other.component))
    result.component["extra"] = extra
    return result


def _method_click(receiver: MCSTextComponent, args, context, *, action: str) -> MCSTextComponent:
    method_name = action.replace("_command", "").replace("_", "_")
    string_arg = _require_string_arg(args, f"click_{action}")
    result = receiver.clone()
    result.component["click_event"] = {
        "action": action,
        "value": _require_literal_string(string_arg, f"TextComponent.click_{action}()"),
    }
    return result


def _method_hover_text(receiver: MCSTextComponent, args, context) -> MCSTextComponent:
    if len(args) != 1:
        raise MCSTypeError(f"TextComponent.hover_text() takes 1 argument, got {len(args)}")

    arg = args[0]
    result = receiver.clone()
    if isinstance(arg, MCSTextComponent):
        hover_value = deepcopy(arg.component)
    elif isinstance(arg, MCSString):
        hover_value = _text_component_from_string(arg)
    else:
        raise MCSTypeError(
            f"TextComponent.hover_text() expects a string or TextComponent, got {arg.class_name()!r}"
        )

    result.component["hover_event"] = {
        "action": "show_text",
        "value": hover_value,
    }
    return result


def _method_hover_item(receiver: MCSTextComponent, args, context) -> MCSTextComponent:
    if not (1 <= len(args) <= 2):
        raise MCSTypeError(f"TextComponent.hover_item() takes 1 or 2 arguments, got {len(args)}")

    item_id = args[0]
    if not isinstance(item_id, MCSString):
        raise MCSTypeError(
            f"TextComponent.hover_item() expects a string item id, got {item_id.class_name()!r}"
        )

    result = receiver.clone()
    hover_value: dict = {
        "id": _require_literal_string(item_id, "TextComponent.hover_item()"),
    }
    if len(args) == 2:
        count = args[1]
        if not isinstance(count, MCSNumber):
            raise MCSTypeError(
                f"TextComponent.hover_item() expects a number count, got {count.class_name()!r}"
            )
        count_value = _literal_number_value(count)
        if count_value is None:
            raise MCSValueError("TextComponent.hover_item() count must be a number literal at compile time")
        hover_value["count"] = count_value

    result.component["hover_event"] = {
        "action": "show_item",
        "value": hover_value,
    }
    return result


def _serialize_for_command(component_source: mcs_type) -> str:
    version = get_version_context()
    config = get_text_component_config(version.orchestration)

    if isinstance(component_source, MCSTextComponent):
        return serialize_component(component_source.component, config)

    if isinstance(component_source, MCSVariable):
        wrapper = component_from_nbt_reference(
            component_source.get_storage(),
            component_source.get_nbt(),
            interpret=True,
        )
        return serialize_component(wrapper, config)

    if isinstance(component_source, MCSString):
        wrapper = component_from_nbt_reference(
            component_source.get_storage(),
            component_source.get_nbt(),
            interpret=True,
        )
        return serialize_component(wrapper, config)

    raise MCSTypeError(
        f"Expected TextComponent or string variable, got {component_source.class_name()!r}"
    )


def _render_text_command(command_key: str, **params) -> str:
    version = get_version_context()
    config = get_text_component_config(version.orchestration)
    template = config["commands"][command_key]
    rendered = template
    for key, value in params.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    return rendered


def text(_interpreter, args, context) -> function_output:
    if len(args) > 1:
        raise MCSTypeError(f"Function text() takes up to 1 argument, got {len(args)}")

    component = MCSTextComponent(context)
    if len(args) == 1:
        if not isinstance(args[0], MCSString):
            raise MCSTypeError(f"Function text() expects a string, got {args[0].class_name()!r}")
        component = _method_text(component, args, context)

    return (), component


def tellraw(_interpreter, args, context) -> function_output:
    if len(args) != 2:
        raise MCSTypeError(f"Function tellraw() takes 2 arguments, got {len(args)}")

    target, component = args
    if not isinstance(target, MCSString):
        raise MCSTypeError(f"tellraw() target must be a string, got {target.class_name()!r}")

    target_value = _require_literal_string(target, "tellraw() target")
    serialized = _serialize_for_command(component)
    command = _render_text_command("tellraw", target=target_value, component=serialized)
    return (command,), MCSNull(context)


def title(_interpreter, args, context) -> function_output:
    if len(args) != 3:
        raise MCSTypeError(f"Function title() takes 3 arguments, got {len(args)}")

    target, mode, component = args
    if not isinstance(target, MCSString):
        raise MCSTypeError(f"title() target must be a string, got {target.class_name()!r}")
    if not isinstance(mode, MCSString):
        raise MCSTypeError(f"title() mode must be a string, got {mode.class_name()!r}")

    target_value = _require_literal_string(target, "title() target")
    mode_value = _require_literal_string(mode, "title() mode")
    if mode_value not in _TITLE_MODES:
        raise MCSValueError(
            f"title() mode must be one of {', '.join(sorted(_TITLE_MODES))!r}, got {mode_value!r}"
        )

    serialized = _serialize_for_command(component)
    command = _render_text_command(
        "title",
        target=target_value,
        mode=mode_value,
        component=serialized,
    )
    return (command,), MCSNull(context)


def title_times(_interpreter, args, context) -> function_output:
    if len(args) != 4:
        raise MCSTypeError(f"Function title_times() takes 4 arguments, got {len(args)}")

    target = args[0]
    fade_in, stay, fade_out = args[1:4]
    if not isinstance(target, MCSString):
        raise MCSTypeError(f"title_times() target must be a string, got {target.class_name()!r}")
    if not all(isinstance(value, MCSNumber) for value in (fade_in, stay, fade_out)):
        raise MCSTypeError("title_times() fadeIn, stay, and fadeOut must be numbers")

    target_value = _require_literal_string(target, "title_times() target")
    fade_in_value = _literal_number_value(fade_in)
    stay_value = _literal_number_value(stay)
    fade_out_value = _literal_number_value(fade_out)
    if None in (fade_in_value, stay_value, fade_out_value):
        raise MCSValueError("title_times() tick values must be number literals at compile time")

    command = _render_text_command(
        "title_times",
        target=target_value,
        fadeIn=fade_in_value,
        stay=stay_value,
        fadeOut=fade_out_value,
    )
    return (command,), MCSNull(context)


def attach_text_component_methods(component: MCSTextComponent) -> MCSTextComponent:
    component.attribute_text = lambda: _bind_method(component, "text", _method_text)
    component.attribute_color = lambda: _bind_method(component, "color", _method_color)
    component.attribute_font = lambda: _bind_method(component, "font", _method_font)
    component.attribute_insertion = lambda: _bind_method(component, "insertion", _method_insertion)
    component.attribute_bold = lambda: _bind_method(
        component, "bold", lambda receiver, args, ctx: _method_formatting_flag(receiver, args, "bold")
    )
    component.attribute_italic = lambda: _bind_method(
        component, "italic", lambda receiver, args, ctx: _method_formatting_flag(receiver, args, "italic")
    )
    component.attribute_underlined = lambda: _bind_method(
        component, "underlined", lambda receiver, args, ctx: _method_formatting_flag(receiver, args, "underlined")
    )
    component.attribute_strikethrough = lambda: _bind_method(
        component,
        "strikethrough",
        lambda receiver, args, ctx: _method_formatting_flag(receiver, args, "strikethrough"),
    )
    component.attribute_obfuscated = lambda: _bind_method(
        component, "obfuscated", lambda receiver, args, ctx: _method_formatting_flag(receiver, args, "obfuscated")
    )
    component.attribute_translate = lambda: _bind_method(component, "translate", _method_translate)
    component.attribute_append = lambda: _bind_method(component, "append", _method_append)
    component.attribute_click_run = lambda: _bind_method(
        component,
        "click_run",
        lambda receiver, args, ctx: _method_click(receiver, args, ctx, action="run_command"),
    )
    component.attribute_click_suggest = lambda: _bind_method(
        component,
        "click_suggest",
        lambda receiver, args, ctx: _method_click(receiver, args, ctx, action="suggest_command"),
    )
    component.attribute_click_open_url = lambda: _bind_method(
        component,
        "click_open_url",
        lambda receiver, args, ctx: _method_click(receiver, args, ctx, action="open_url"),
    )
    component.attribute_click_copy = lambda: _bind_method(
        component,
        "click_copy",
        lambda receiver, args, ctx: _method_click(receiver, args, ctx, action="copy_to_clipboard"),
    )
    component.attribute_hover_text = lambda: _bind_method(component, "hover_text", _method_hover_text)
    component.attribute_hover_item = lambda: _bind_method(component, "hover_item", _method_hover_item)
    return component
