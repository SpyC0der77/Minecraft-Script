from copy import deepcopy

from ..common import generate_uuid
from ..text_components import get_text_component_config, serialize_component
from ..version_config import get_version_context


class MCSObject:
    def __init__(self, context, storage_compartment: str):
        self.context = context
        self.uuid = generate_uuid()
        self.storage_compartment = storage_compartment

    def class_name(self) -> str:
        name = self.__class__.__name__
        return name[3:] if name.startswith("MCS") else name

    def get_nbt(self) -> str:
        return f"{self.storage_compartment}.{self.uuid}"

    def get_storage(self) -> str:
        return f"mcs_{self.context.uuid}"

    def save_to_storage_cmd(self, value: any) -> str:
        return get_version_context().render(
            "literal.save",
            storage=self.get_storage(),
            nbt=self.get_nbt(),
            value=value,
        )

    def delete_from_storage_cmd(self) -> str:
        return get_version_context().render(
            "literal.delete",
            storage=self.get_storage(),
            nbt=self.get_nbt(),
        )

    def set_to_current_cmd(self, output_context) -> str:
        return get_version_context().render(
            "literal.set_to_current",
            destStorage=f"mcs_{output_context.uuid}",
            storage=self.get_storage(),
            nbt=self.get_nbt(),
        )


class MCSVariable:
    def __init__(self, name: str, context):
        self.name = name
        self.context = context

    def get_nbt(self) -> str:
        return f"variable.{self.name}"

    def get_storage(self) -> str:
        return f"mcs_{self.context.uuid}"

    def set_to_current_cmd(self, output_context) -> str:
        return get_version_context().render(
            "literal.set_to_current",
            destStorage=f"mcs_{output_context.uuid}",
            storage=self.get_storage(),
            nbt=self.get_nbt(),
        )

    def __repr__(self) -> str:
        return f"MCSVariable({self.name !r}, {self.context.uuid !r})"


class MCSList(MCSObject):
    def __init__(self, context):
        super().__init__(context, "list")

    def save_to_storage_cmd(self, values: list["mcs_type"]) -> list[str]:
        version = get_version_context()
        commands = [
            version.render(
                "literal.list.length",
                storage=self.get_storage(),
                nbt=self.get_nbt(),
                length=len(values),
            )
        ]

        for i, value in enumerate(values):
            commands.extend((
                value.set_to_current_cmd(self.context),
                version.render(
                    "literal.list.element",
                    storage=self.get_storage(),
                    nbt=self.get_nbt(),
                    index=i,
                    srcStorage=self.get_storage(),
                ),
            ))

        return commands

    def __repr__(self) -> str:
        return f"MCSList({self.uuid})"


class MCSNull(MCSObject):
    def __init__(self, context):
        super().__init__(context, "null")

    def save_to_storage_cmd(self) -> str:
        return get_version_context().render(
            "literal.save",
            storage=self.get_storage(),
            nbt=self.get_nbt(),
            value="0b",
        )

    def set_to_current_cmd(self, output_context) -> str:
        return get_version_context().render(
            "literal.save",
            storage=f"mcs_{output_context.uuid}",
            nbt="current",
            value="0b",
        )

    def __repr__(self) -> str:
        return "MCSNull()"


class MCSNumber(MCSObject):
    def __init__(self, context):
        super().__init__(context, "number")

    def __repr__(self) -> str:
        return f"MCSNumber({self.uuid !r})"


class MCSString(MCSObject):
    def __init__(self, context):
        super().__init__(context, "string")

    def __repr__(self) -> str:
        return f"MCSString({self.uuid !r})"


class MCSTextComponent(MCSObject):
    def __init__(self, context, component: dict | None = None):
        super().__init__(context, "text_component")
        self.component = dict(component or {})
        from .text_component_builtins import attach_text_component_methods

        attach_text_component_methods(self)

    def clone(self) -> "MCSTextComponent":
        cloned = MCSTextComponent(self.context, deepcopy(self.component))
        return cloned

    def save_to_storage_cmd(self, value: any = None) -> str:
        config = get_text_component_config(get_version_context().orchestration)
        serialized = serialize_component(self.component, config)
        return super().save_to_storage_cmd(repr(serialized))

    def attribute_not_present(self, name: str):
        raise AttributeError(f"TextComponent has no attribute {name!r}")

    def __repr__(self) -> str:
        return f"MCSTextComponent({self.uuid !r})"


class MCSBoolean(MCSObject):
    def __init__(self, context):
        super().__init__(context, "boolean")

    def __repr__(self) -> str:
        return f"MCSBoolean({self.uuid !r})"


class MCSUnknown(MCSObject):
    def __init__(self, context):
        super().__init__(context, "unknown")

    def __repr__(self) -> str:
        return f"MCSUnknown({self.uuid !r})"


class MCSFunction:
    def __init__(self, name: str, body, parameter_names: list[str, ...], context):
        from .compile_interpreter import CompileContext

        self.name = name
        self.body = body
        self.parameter_names = parameter_names
        self.local_context = CompileContext(self.name, parent=context)

    def generate_function(self, interpreter) -> None:
        for name in self.parameter_names:
            self.local_context.declare(name, MCSVariable(name, self.local_context))

        interpreter.visit(self.body, self.local_context)

    def call(self, interpreter, arguments, context) -> tuple[list, "mcs_type"]:
        version = get_version_context()
        commands = []

        for name, argument in zip(self.parameter_names, arguments, strict=True):
            commands.extend(version.render_lines(
                "function.call.param",
                localStorage=f"mcs_{self.local_context.uuid}",
                argStorage=argument.get_storage(),
                argNbt=argument.get_nbt(),
                paramName=name,
            ))

        commands.append(version.render(
            "function.call.invoke",
            functionName=self.name,
        ))

        return commands, MCSNull(context)

    def __repr__(self) -> str:
        return f"MCSFunction({self.name !r})"


mcs_type = (
    MCSNull
    | MCSNumber
    | MCSString
    | MCSBoolean
    | MCSUnknown
    | MCSList
    | MCSFunction
    | MCSVariable
    | MCSTextComponent
)
