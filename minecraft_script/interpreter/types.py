from ..errors import *

operation_lookup_table = {
    "&&": "logical_and",
    "||": "logical_or",
}


class MCSObject:
    def get_value(self):
        raise MCSInterpreterError('Failed getting value of unknown Object')

    def get_key(self, key):
        raise MCSTypeError(f'{self.class_name() !r} is not subscriptable')

    def call(self, *args):
        raise MCSTypeError(f'{self.class_name() !r} is not callable')

    def class_name(self) -> str:
        return self.__class__.__name__[3:]

    def print_value(self) -> str:
        return str(self.get_value())

    def repr_value(self) -> str:
        return repr(self.get_value())

    def is_iterable(self) -> bool:
        return False

    # ----------------- Attributes  ----------------- :
    def attribute_not_present(self, name: str):
        raise MCSAttributeError(f"Type {self.class_name() !r} has no attribute {name !r}")

    # ----------------- Operations  ----------------- :
    def _binary_operation(self, other, operator: str):
        if isinstance(other, self.__class__):
            return MCSNumber(eval(f"self.value {operator} other.get_value()"))

        raise self.operation_error(other, f'"{operator}"')

    def add(self, other):
        return self._binary_operation(other, '+')

    def subtract(self, other):
        return self._binary_operation(other, '-')

    def multiply(self, other):
        return self._binary_operation(other, '*')

    def divide(self, other):
        return self._binary_operation(other, '//')

    def modulus(self, other):
        return self._binary_operation(other, '%')

    def unary_operation(self, operator: str):
        if operator == 'not':
            return MCSBool(not bool(self.get_value()))

        raise MCSTypeError(f'Unsupported unary operand {operator !r} for type {self.class_name() !r}')

    def operation_error(self, other, operation):
        return MCSTypeError(
            f"Unsupported operand types for {operation if operation != '//' else '/' !r}: "
            f"{self.class_name() !r} and {other.class_name() !r}"
        )

    # ----------------- Comparisons ----------------- :
    def _comparison_operation(self, other, comparator: str):
        try:
            result = eval(f"self.get_value() {comparator} other.get_value()")
        except TypeError as err:
            raise self.comparison_error(other, comparator) from err
        else:
            return MCSBool(result)

    def equals(self, other):
        return self._comparison_operation(other, '==')

    def less_than(self, other):
        return self._comparison_operation(other, '<')

    def greater_than(self, other):
        return self._comparison_operation(other, '>')

    def less_equals_than(self, other):
        return self._comparison_operation(other, '<=')

    def greater_equals_than(self, other):
        return self._comparison_operation(other, '>=')

    def comparison_error(self, other, comparator: str):
        return MCSTypeError(
            f"{comparator !r} not supported between instances of "
            f"{self.class_name() !r} and {other.class_name() !r}"
        )

    # ----------------- Boolean Connectors ----------------- :
    def boolean_and(self, other):
        return MCSBool(self.get_value() and other.get_value())

    def boolean_or(self, other):
        return MCSBool(bool(self.get_value() or other.get_value()))  # have to call bool() here since "5 or 3 == 5"

    # ----------------- Miscellaneous  ----------------- :
    def __bool__(self):
        return bool(self.get_value())


class MCSIterable(MCSObject):
    def get_key(self, key: str) -> any:
        try:
            index = int(key)
        except ValueError as err:
            raise MCSTypeError(f'{self.class_name()} indices must be integers') from err

        return self.get_value()[index]

    def set_key(self, key: str, value: any) -> None:
        try:
            index = int(key)
        except ValueError as err:
            raise MCSTypeError(f'{self.class_name()} indices must be integers') from err

        if index < len(self.get_value()):
            self.get_value()[index] = value
        else:
            self.get_value().insert(index, value)

    def is_iterable(self) -> bool:
        return True

    # ----------------- Attributes ----------------- :
    def attribute_length(self) -> "MCSNumber":
        return MCSNumber(len(self.get_value()))


class MCSNumber(MCSObject):
    def __init__(self, value: int):
        if not isinstance(value, int):
            raise MCSInterpreterError(f"Expected type 'int', got {value.__class__.__name__ !r}")

        self.value = value

    def get_value(self) -> int:
        return self.value

    def unary_operation(self, operator: str):
        if operator == 'add':
            return self
        elif operator == 'subtract':
            return MCSNumber(-self.value)  # Number with opposite value

        return super().unary_operation(operator)

    # ----------------- Miscellaneous ----------------- :
    def __int__(self) -> int:
        return self.get_value()

    def __repr__(self) -> str:
        return f'MCSNumber({self.value !r})'


class MCSBool(MCSObject):
    def __init__(self, value: bool):
        if not isinstance(value, bool):
            raise MCSInterpreterError(f"Expected type 'bool', got {value.__class__.__name__ !r}")

        self.value = value

    def get_value(self) -> bool:
        return self.value

    def print_value(self) -> str:
        return "true" if self.value else "false"

    def repr_value(self) -> str:
        return self.print_value()  # same as print value


class MCSNull(MCSObject):
    def get_value(self) -> None:
        return

    def print_value(self) -> str:
        return f"null"

    # ----------------- Operations ----------------- :
    def _binary_operation(self, other, operator: str):
        if isinstance(other, (MCSNumber, MCSNull)):
            return MCSNumber(eval(f"0 {operator} other.get_value()"))

        raise self.operation_error(other, repr(operator))

    # ----------------- Miscellaneous ----------------- :
    def __repr__(self) -> str:
        return f'MCSNull()'


class MCSString(MCSIterable, MCSObject):
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise MCSInterpreterError(f"Expected type 'str', got {value.__class__.__name__ !r}")
        self.value = value

    def get_value(self) -> str:
        return self.value

    def get_key(self, key: str) -> "MCSString":
        return MCSString(super().get_key(key))

    # ----------------- Operations ----------------- :
    def _binary_operation(self, other, operator: str):
        if operator in ('//', '%'):  # invalid operations
            raise self.operation_error(other, operator)

        if isinstance(other, MCSString if operator in ('+', '-') else (MCSNumber, MCSNull)):
            return MCSString(eval(f"self.value {operator} other.get_value()"))

        raise self.operation_error(other, operator)

    # ----------------- Miscellaneous ----------------- :
    def __repr__(self) -> str:
        return f"MCSString({self.value !r})"


class MCSList(MCSIterable, MCSObject):
    def __init__(self, value: list | tuple):
        if not isinstance(value, (list, tuple)):
            raise MCSInterpreterError(f"Expected type 'list' or 'tuple', got {value.__class__.__name__ !r}")

        self.value = list(value)

    def get_value(self) -> list:
        return self.value

    def print_value(self) -> str:
        return f"[{', '.join(value.repr_value() for value in self.value)}]"

    # ----------------- Attributes ----------------- :
    def attribute_append(self) -> "MCSFunction":
        def fnc_call(call_args: list, context):
            from .interpreter import RuntimeResult
            if len(call_args) != 1:
                raise MCSTypeError(f"Function <List.append> takes 1 argument, got {len(call_args)}")

            self.value.append(call_args[0])  # append value to list

            return RuntimeResult(return_value=MCSNull())

        fnc = MCSFunction("List.append", None, None)
        fnc.call = fnc_call

        return fnc

    # ----------------- Operations ----------------- :
    def _binary_operation(self, other, operator: str):
        if operator in ('//', '%', '-'):  # invalid operations
            raise self.operation_error(other, operator)

        if isinstance(other, MCSList):
            return MCSList(self.value + other.get_value())

        raise self.operation_error(other, operator)

    # ----------------- Miscellaneous ----------------- :
    def __repr__(self) -> str:
        return f'MCSList({self.value !r})'


class MCSTextComponent(MCSObject):
    def __init__(self, component: dict | None = None):
        from copy import deepcopy

        self.component = deepcopy(component) if component else {}

    def get_value(self) -> dict:
        return self.component

    def print_value(self) -> str:
        return str(self.component)

    def clone(self) -> "MCSTextComponent":
        from copy import deepcopy

        return MCSTextComponent(deepcopy(self.component))

    def _bind(self, method_name: str, handler):
        receiver = self

        def fnc_call(call_args: list, context):
            from .interpreter import RuntimeResult

            return RuntimeResult(return_value=handler(receiver, call_args))

        fnc = MCSFunction(f"TextComponent.{method_name}", None, None)
        fnc.call = fnc_call
        return fnc

    def attribute_text(self):
        return self._bind("text", _runtime_text)

    def attribute_color(self):
        return self._bind("color", _runtime_color)

    def attribute_font(self):
        return self._bind("font", _runtime_font)

    def attribute_insertion(self):
        return self._bind("insertion", _runtime_insertion)

    def attribute_bold(self):
        return self._bind("bold", lambda receiver, args: _runtime_flag(receiver, args, "bold"))

    def attribute_italic(self):
        return self._bind("italic", lambda receiver, args: _runtime_flag(receiver, args, "italic"))

    def attribute_underlined(self):
        return self._bind("underlined", lambda receiver, args: _runtime_flag(receiver, args, "underlined"))

    def attribute_strikethrough(self):
        return self._bind("strikethrough", lambda receiver, args: _runtime_flag(receiver, args, "strikethrough"))

    def attribute_obfuscated(self):
        return self._bind("obfuscated", lambda receiver, args: _runtime_flag(receiver, args, "obfuscated"))

    def attribute_translate(self):
        return self._bind("translate", _runtime_translate)

    def attribute_append(self):
        return self._bind("append", _runtime_append)

    def attribute_click_run(self):
        return self._bind("click_run", lambda receiver, args: _runtime_click(receiver, args, "run_command"))

    def attribute_click_suggest(self):
        return self._bind("click_suggest", lambda receiver, args: _runtime_click(receiver, args, "suggest_command"))

    def attribute_click_open_url(self):
        return self._bind("click_open_url", lambda receiver, args: _runtime_click(receiver, args, "open_url"))

    def attribute_click_copy(self):
        return self._bind("click_copy", lambda receiver, args: _runtime_click(receiver, args, "copy_to_clipboard"))

    def attribute_hover_text(self):
        return self._bind("hover_text", _runtime_hover_text)

    def attribute_hover_item(self):
        return self._bind("hover_item", _runtime_hover_item)


class MCSModule(MCSObject):
    def __init__(self, name: str, context):
        self.name = name
        self.context = context

    def get_value(self):
        raise MCSInterpreterError("Can't get value of module")

    def print_value(self) -> str:
        return f"<module-{self.name}>"

    def repr_value(self) -> str:
        return self.print_value()

    def __getattr__(self, name: str):
        if not name.startswith("attribute_"):
            raise AttributeError(name)

        attribute_name = name[len("attribute_"):]
        return lambda: self.context.get(attribute_name)

    def __repr__(self) -> str:
        return f"MCSModule({self.name !r})"


def _runtime_require_string(args, method_name: str) -> MCSString:
    if len(args) != 1 or not isinstance(args[0], MCSString):
        raise MCSTypeError(f"TextComponent.{method_name}() expects one string argument")
    return args[0]


def _runtime_text(receiver: MCSTextComponent, args) -> MCSTextComponent:
    string_arg = _runtime_require_string(args, "text")
    result = receiver.clone()
    result.component = {"text": string_arg.get_value()}
    return result


def _runtime_color(receiver: MCSTextComponent, args) -> MCSTextComponent:
    string_arg = _runtime_require_string(args, "color")
    result = receiver.clone()
    result.component["color"] = string_arg.get_value()
    return result


def _runtime_font(receiver: MCSTextComponent, args) -> MCSTextComponent:
    string_arg = _runtime_require_string(args, "font")
    result = receiver.clone()
    result.component["font"] = string_arg.get_value()
    return result


def _runtime_insertion(receiver: MCSTextComponent, args) -> MCSTextComponent:
    string_arg = _runtime_require_string(args, "insertion")
    result = receiver.clone()
    result.component["insertion"] = string_arg.get_value()
    return result


def _runtime_flag(receiver: MCSTextComponent, args, flag_name: str) -> MCSTextComponent:
    if len(args) != 0:
        raise MCSTypeError(f"TextComponent.{flag_name}() takes 0 arguments")
    result = receiver.clone()
    result.component[flag_name] = True
    return result


def _runtime_translate(receiver: MCSTextComponent, args) -> MCSTextComponent:
    string_arg = _runtime_require_string(args, "translate")
    result = receiver.clone()
    result.component = {"translate": string_arg.get_value()}
    return result


def _runtime_append(receiver: MCSTextComponent, args) -> MCSTextComponent:
    if len(args) != 1 or not isinstance(args[0], MCSTextComponent):
        raise MCSTypeError("TextComponent.append() expects one TextComponent argument")
    result = receiver.clone()
    if not result.component:
        return args[0].clone()
    extra = list(result.component.get("extra", []))
    extra.append(args[0].clone().component)
    result.component["extra"] = extra
    return result


def _runtime_click(receiver: MCSTextComponent, args, action: str) -> MCSTextComponent:
    string_arg = _runtime_require_string(args, f"click_{action}")
    result = receiver.clone()
    result.component["click_event"] = {"action": action, "value": string_arg.get_value()}
    return result


def _runtime_hover_text(receiver: MCSTextComponent, args) -> MCSTextComponent:
    if len(args) != 1:
        raise MCSTypeError("TextComponent.hover_text() expects one argument")
    result = receiver.clone()
    if isinstance(args[0], MCSTextComponent):
        hover_value = args[0].clone().component
    elif isinstance(args[0], MCSString):
        hover_value = {"text": args[0].get_value()}
    else:
        raise MCSTypeError("TextComponent.hover_text() expects a string or TextComponent")
    result.component["hover_event"] = {"action": "show_text", "value": hover_value}
    return result


def _runtime_hover_item(receiver: MCSTextComponent, args) -> MCSTextComponent:
    if not (1 <= len(args) <= 2):
        raise MCSTypeError("TextComponent.hover_item() expects one or two arguments")
    if not isinstance(args[0], MCSString):
        raise MCSTypeError("TextComponent.hover_item() expects a string item id")
    result = receiver.clone()
    hover_value = {"id": args[0].get_value()}
    if len(args) == 2:
        if not isinstance(args[1], MCSNumber):
            raise MCSTypeError("TextComponent.hover_item() expects a number count")
        hover_value["count"] = args[1].get_value()
    result.component["hover_event"] = {"action": "show_item", "value": hover_value}
    return result


class MCSFunction(MCSObject):
    def __init__(self, name: str, body, parameter_names: tuple[str, ...], context=None):
        self.name = name if name is not None else "anonymous function"
        self.body = body
        self.parameter_names = parameter_names
        self.context = context

    def get_value(self):
        raise MCSInterpreterError("Can't get value of function")

    def print_value(self) -> str:
        return f'<{self.name}>'

    def repr_value(self) -> str:
        return self.print_value()

    def call(self, arg_list: list | None, context):
        from .interpreter import Interpreter, InterpreterContext, RuntimeResult
        local_interpreter = Interpreter()
        local_context = InterpreterContext(parent=self.context or context)  # top level always false here

        if len(arg_list) != len(self.parameter_names):
            raise MCSValueError(f"Function {self.print_value()} takes {len(self.parameter_names)} arguments, got {len(arg_list)}")

        # Add argument values to parameter names in local context (to make arguments work)
        for i in range(len(self.parameter_names)):
            local_context.declare(self.parameter_names[i], arg_list[i])

        result: RuntimeResult = local_interpreter.visit(self.body, local_context)

        return result if result.get_return_value() is not None else RuntimeResult(return_value=MCSNull())

    def __repr__(self) -> str:
        return f"MCSFunction({self.name !r}, {self.parameter_names !r})"
