from .builtin_functions import builtin_functions
from .text_component_builtins import text, tellraw, title, title_times
from .compile_types import *
from ..common import COMMON_CONFIG
from ..version_config import get_version_context
from pathlib import Path
import re


SCOREBOARD_CRITERIA_PATTERN = re.compile(r"^[A-Za-z0-9_./:-]+$")

def add_comment(commands: tuple | list | str, comment: str) -> tuple | str:
    if not isinstance(commands, (tuple, list, str)):
        raise ValueError("Commands have to be tuple, list, or str")
    if COMMON_CONFIG["debug_comments"] is False:
        return tuple(commands) if isinstance(commands, list) else commands
    if isinstance(commands, list):
        commands = tuple(commands)
    if isinstance(commands, tuple):
        return (f"\n# {comment}",) + commands
    return f"\n# {comment}\n" + commands

class CompileSymbols:
    def __init__(self, parent: "CompileSymbols" = None, *, load_builtins: bool = False):
        self.symbols: dict[str, mcs_type] = {}
        self.parent = parent
        if load_builtins:
            self.load_builtins()
    def load_builtins(self) -> None:
        function_name_lookup = {
            "mcs_range": "range"
        }
        for fnc in (*builtin_functions, text, tellraw, title, title_times):
            mcs_fnc = MCSFunction(None, None, None, None)
            mcs_fnc.call = fnc
            self.declare(
                function_name_lookup.get(fnc.__name__, fnc.__name__),
                mcs_fnc
            )
    def get(self, name: str, *, raise_error=True) -> mcs_type:
        value = self.symbols.get(name, None)
        if value is not None:
            return value
        if self.parent is not None:
            return self.parent.get(name)
        raise NameError(f"name {name !r} is not defined")
    def set(self, name: str, value: mcs_type) -> None:
        if self.symbols.get(name, None) is not None:
            self.symbols[name] = value
            return
        if self.parent is not None:
            self.parent.set(name, value)
            return
        raise NameError(f"name {name !r} has not been declared")
    def declare(self, name: str, value: mcs_type) -> None:
        self.symbols[name] = value
    def __repr__(self) -> str:
        return f'CompileSymbols({self.parent !r})'

class CompileContext:
    def __init__(self, mcfunction_name: str = None, *, parent: "CompileContext" = None, top_level: bool = False):
        self.parent: CompileContext = parent
        self.symbols = CompileSymbols(parent.symbols if parent is not None else None, load_builtins=top_level)
        self.top_level = top_level
        self._mcfunction_name = mcfunction_name if mcfunction_name is not None else f":cb_{generate_uuid()}"
        self.uuid = generate_uuid()
    @property
    def mcfunction_name(self) -> str:
        return (
            f"user_functions/{self._mcfunction_name}"
            if self._mcfunction_name[0] != ":" else
            f"code_blocks/{self._mcfunction_name[1:]}"
        )
    def get(self, name: str) -> mcs_type:
        return self.symbols.get(name)
    def set(self, name: str, value: mcs_type):
        return self.symbols.set(name, value)
    def declare(self, name: str, value: mcs_type) -> None:
        self.symbols.declare(name, value)
    def get_context_ownership(self, var_name: str) -> "CompileContext":
        if self.symbols.symbols.get(var_name, None) is not None:
            return self
        if self.parent is not None:
            return self.parent.get_context_ownership(var_name)
        raise NameError(f"name {var_name} is not defined")
    def __repr__(self) -> str:
        return f'CompileContext({self._mcfunction_name !r}, {self.parent !r}, {self.top_level !r})'

class CompileCommands:
    def __init__(self):
        self.commands: dict[str, list[str]] = {}
    def add_command(self, mcfunction, command) -> None:
        current_commands = self.commands.get(mcfunction, None)
        if current_commands is not None:
            current_commands.append(command)
            return
        self.commands[mcfunction] = [command]
    def get_file_content(self, mcfunction_file_name: str) -> str:
        return "\n".join(self.commands.get(mcfunction_file_name, []))
    def get_mcs_functions(self) -> tuple[str, ...]:
        return tuple(self.commands.keys())
    def __repr__(self) -> str:
        return "CompileCommands()"

class CompileResult:
    def __init__(self, value: mcs_type = None, return_value: mcs_type = None):
        self.value = value
        self.return_value = return_value
    def get_value(self) -> mcs_type | None:
        return self.value
    def get_return(self) -> mcs_type | None:
        return self.return_value
    def __repr__(self) -> str:
        return f"CompileResult({self.value}, {self.return_value})"

class CompileInterpreter:
    def __init__(self, datapack_id):
        self.datapack_id = datapack_id
        self.version = get_version_context()
        self.commands = CompileCommands()
        self.used_context_ids = set()
        self.functions_to_generate = set()
        self.click_item_lookup = dict()
        self.used_math_builtins = set()
        self.used_builtin_functions = set()
        self.scoreboard_event_functions = []

    def get_scoreboard_event_hooks(self) -> list[dict[str, str]]:
        hooks = []
        for index, function in enumerate(self.scoreboard_event_functions):
            hooks.append({
                "function_name": function.name,
                "criteria": function.event_criteria,
                "scoreboard": f"mcs_on_{index}",
            })
        return hooks
    def add_command(self, mcfunction: str, command: str | None) -> None:
        if command is not None:
            self.commands.add_command(mcfunction, command)
    def add_commands(self, mcfunction: str, commands: iter) -> None:
        multiline_command = "\n".join(commands)
        self.add_command(mcfunction, multiline_command)
    def get_file_content(self, mcfunction):
        return self.commands.get_file_content(mcfunction)
    def get_mcs_functions(self) -> tuple[str, ...]:
        return self.commands.get_mcs_functions()
    def visit(self, node, context: CompileContext) -> CompileResult:
        if context.uuid not in self.used_context_ids:
            self.used_context_ids.add(context.uuid)
        method = getattr(self, f"visit_{type(node).__name__}", self.visit_unknown)
        return method(node, context)
    def visit_NumberNode(self, node, context: CompileContext) -> CompileResult:
        value = int(node.get_value())
        obj = MCSNumber(context)
        obj.literal_value = value
        self.add_command(context.mcfunction_name, obj.save_to_storage_cmd(value))
        result = CompileResult(obj)
        return result
    def visit_StringNode(self, node, context: CompileContext) -> CompileResult:
        value = repr(node.get_value())
        mcs_obj = MCSString(context)
        mcs_obj.literal_value = node.get_value()
        self.add_command(context.mcfunction_name, mcs_obj.save_to_storage_cmd(value))
        result = CompileResult(mcs_obj)
        return result
    def visit_ListNode(self, node, context: CompileContext) -> CompileResult:
        value_list: list[mcs_type] = list(map(lambda x: self.visit(x, context).get_value(), node.get_node_list()))
        mcs_obj = MCSList(context)
        self.add_commands(context.mcfunction_name, mcs_obj.save_to_storage_cmd(value_list))
        result = CompileResult(mcs_obj)
        return result
    def visit_BooleanNode(self, node, context: CompileContext) -> CompileResult:
        boolean: bool = node.get_value()
        mcs_obj = MCSBoolean(context)
        value = "1" if boolean is True else "0"
        self.add_command(context.mcfunction_name, mcs_obj.save_to_storage_cmd(value))
        result = CompileResult(mcs_obj)
        return result
    @staticmethod
    def visit_NullNode(node, context: CompileContext) -> CompileResult:
        mcs_obj = MCSNull(context)
        return CompileResult(mcs_obj)
    def visit_DefineFunctionNode(self, node, context: CompileContext) -> CompileResult:
        fnc_name = node.get_name()
        fnc_body = node.get_body()
        fnc_parameter_names: list[str, ...] = node.get_parameter_names()
        event_criteria = node.get_event_criteria()
        if event_criteria is not None:
            if fnc_parameter_names:
                raise ValueError(f"Event function {fnc_name!r} cannot have parameters")
            if SCOREBOARD_CRITERIA_PATTERN.fullmatch(event_criteria) is None:
                raise ValueError(f"Invalid scoreboard criteria {event_criteria!r}")
        function = MCSFunction(fnc_name, fnc_body, fnc_parameter_names, context, event_criteria)
        self.functions_to_generate.add(function)
        if event_criteria is not None:
            self.scoreboard_event_functions.append(function)
        context.declare(fnc_name, function)
        return CompileResult(function)
    def visit_VariableDeclareNode(self, node, context: CompileContext) -> CompileResult:
        variable_name: str = node.get_name()
        variable_value: mcs_type = node.get_value()
        if variable_value is None:
            context.declare(variable_name, MCSNull(context))
            return CompileResult()
        variable_value = self.visit(variable_value, context).get_value()
        commands = []
        if isinstance(variable_value, MCSTextComponent):
            commands.append(variable_value.save_to_storage_cmd())
        commands.append(
            self.version.render(
                "variable.declare",
                ownerStorage=f"mcs_{context.uuid}",
                name=variable_name,
                valueStorage=variable_value.get_storage(),
                valueNbt=variable_value.get_nbt(),
            ),
        )
        if not isinstance(variable_value, MCSVariable):
            commands.append(variable_value.delete_from_storage_cmd())
        self.add_commands(context.mcfunction_name, commands)
        variable = MCSVariable(variable_name, context)
        context.declare(variable_name, variable)
        return CompileResult()
    def visit_VariableAccessNode(self, node, context: CompileContext) -> CompileResult:
        variable_name: str = node.get_name()
        value: mcs_type = context.get(variable_name)
        return CompileResult(value)
    def visit_AttributeGetNode(self, node, context: CompileContext) -> CompileResult:
        root: mcs_type = self.visit(node.get_root(), context).get_value()
        attribute_name: str = node.get_name()
        attribute = getattr(root, f"attribute_{attribute_name}", None)
        if attribute is None:
            if hasattr(root, "attribute_not_present"):
                root.attribute_not_present(attribute_name)
            raise AttributeError(f"Type {type(root).__name__} has no attribute {attribute_name!r}")
        return CompileResult(attribute())
    def visit_VariableSetNode(self, node, context: CompileContext) -> CompileResult:
        var_name = node.get_name()
        new_value: mcs_type = self.visit(node.get_value(), context).get_value()
        owner_context = context.get_context_ownership(var_name)
        command = self.version.render(
            "variable.assign",
            ownerStorage=f"mcs_{owner_context.uuid}",
            name=var_name,
            valueStorage=new_value.get_storage(),
            valueNbt=new_value.get_nbt(),
        )
        self.add_command(context.mcfunction_name, command)
        return CompileResult()
    def visit_GetKeyNode(self, node, context: CompileContext) -> CompileResult:
        atom: mcs_type = self.visit(node.get_atom(), context).get_value()
        key: MCSNumber = self.visit(node.get_key(), context).get_value()
        result = MCSUnknown(context)
        local_context = CompileContext(parent=context)
        self.add_command(
            local_context.mcfunction_name,
            self.version.render(
                "index.macro",
                resultStorage=result.get_storage(),
                resultNbt=result.get_nbt(),
                atomStorage=atom.get_storage(),
                atomNbt=atom.get_nbt(),
            ),
        )
        commands = self.version.render_lines(
            "index.setup",
            ctxStorage=f"mcs_{context.uuid}",
            keyStorage=key.get_storage(),
            keyNbt=key.get_nbt(),
            macroPath=local_context.mcfunction_name,
        )
        commands = add_comment(commands, f"Get key (from {atom.get_nbt() !r})")
        self.add_commands(context.mcfunction_name, commands)
        return CompileResult(result)
    def visit_IfConditionNode(self, node, context: CompileContext) -> CompileResult:
        conditions: list[dict] = node.get_conditions()
        local_context = CompileContext(parent=context)
        init_commands = self.version.render_lines(
            "control.if.init",
            ifPath=local_context.mcfunction_name,
        )
        init_commands = add_comment(init_commands, "If condition block")
        self.add_commands(context.mcfunction_name, init_commands)
        for condition in conditions:
            sublocal_context = CompileContext(parent=local_context)
            out: CompileResult = self.visit(condition.get('body'), sublocal_context)
            if condition.get('type') == 'if':
                expression: MCSNumber = self.visit(condition.get('expression'), context).get_value()
                commands = self.version.render_lines(
                    "control.if.branch",
                    exprStorage=expression.get_storage(),
                    exprNbt=expression.get_nbt(),
                    branchStorage=f"mcs_{sublocal_context.uuid}",
                    parentStorage=f"mcs_{context.uuid}",
                    branchPath=sublocal_context.mcfunction_name,
                )
                commands = add_comment(commands, "If condition:")
                self.add_commands(local_context.mcfunction_name, commands)
            else:
                commands = self.version.render_lines(
                    "control.if.else",
                    branchPath=sublocal_context.mcfunction_name,
                )
                commands = add_comment(commands, "Else condition:")
                self.add_commands(local_context.mcfunction_name, commands)
            if out.get_return() is not None:
                return out
        return CompileResult()
    def visit_ForLoopNode(self, node, context: CompileContext) -> CompileResult:
        iterable: MCSList = self.visit(node.get_iterable(), context).get_value()
        element_name: str = node.get_child_name()
        body = node.get_body()
        local_context = CompileContext(parent=context)
        macro_context = CompileContext(parent=context)
        loop_id = f"{generate_uuid()}"
        init_commands = self.version.render_lines(
            "control.for.init",
            loopId=loop_id,
            iterableStorage=iterable.get_storage(),
            iterableNbt=iterable.get_nbt(),
            loopPath=local_context.mcfunction_name,
        )
        init_commands = add_comment(init_commands, f"For loop (variable {element_name !r})")
        self.add_commands(context.mcfunction_name, init_commands)
        macro_cmd = self.version.render(
            "control.for.macro",
            loopStorage=f"mcs_{local_context.uuid}",
            elementName=element_name,
            iterableStorage=iterable.get_storage(),
            iterableNbt=iterable.get_nbt(),
        )
        self.add_command(macro_context.mcfunction_name, macro_cmd)
        loop_init_commands = self.version.render_lines(
            "control.for.body_setup",
            loopStorage=f"mcs_{local_context.uuid}",
            loopId=loop_id,
            macroPath=macro_context.mcfunction_name,
        )
        self.add_commands(local_context.mcfunction_name, loop_init_commands)
        local_context.declare(element_name, MCSVariable(element_name, local_context))
        out: CompileResult = self.visit(body, local_context)
        loop_end_commands = self.version.render_lines(
            "control.for.loop_end",
            loopId=loop_id,
            loopPath=local_context.mcfunction_name,
        )
        self.add_commands(local_context.mcfunction_name, loop_end_commands)
        if out.get_return() is not None:
            return out
        return CompileResult()
    def visit_WhileLoopNode(self, node, context: CompileContext) -> CompileResult:
        loop_context = CompileContext(parent=context)
        init_cmd = self.version.render("control.while.init", loopPath=loop_context.mcfunction_name)
        if COMMON_CONFIG["debug_comments"] is True:
            init_cmd = f"# Initialize while loop:\n{init_cmd}"
        self.add_command(context.mcfunction_name, init_cmd)
        out: CompileResult = self.visit(node.get_body(), loop_context)
        condition: mcs_type = self.visit(node.get_condition(), loop_context).get_value()
        loop_commands = self.version.render_lines(
            "control.while.tail",
            condStorage=condition.get_storage(),
            condNbt=condition.get_nbt(),
            loopPath=loop_context.mcfunction_name,
        )
        loop_commands = add_comment(loop_commands, f"While loop:")
        self.add_commands(loop_context.mcfunction_name, loop_commands)
        return out if out.get_return() is not None else CompileResult()
    def visit_AsyncWhileLoopNode(self, node, context: CompileContext) -> CompileResult:
        loop_context = CompileContext(parent=context)
        schedule_context = CompileContext(parent=context)
        selector_context = CompileContext(parent=context)
        condition_context = CompileContext(parent=context)
        selector_id = generate_uuid()
        out: CompileResult = self.visit(node.get_body(), loop_context)
        condition: mcs_type = self.visit(node.get_condition(), condition_context).get_value()
        loop_init_cmd = self.version.render(
            "control.async_while.init",
            conditionPath=condition_context.mcfunction_name,
        )
        loop_init_cmd = add_comment(loop_init_cmd, "Initialize async while loop:")
        self.add_command(context.mcfunction_name, loop_init_cmd)
        condition_commands = self.version.render_lines(
            "control.async_while.condition",
            condStorage=condition.get_storage(),
            condNbt=condition.get_nbt(),
            loopPath=loop_context.mcfunction_name,
        )
        loop_condition_commands = add_comment(condition_commands, f"Async While Loop (condition segment - {context.mcfunction_name !r}):")
        self.add_commands(condition_context.mcfunction_name, loop_condition_commands)
        loop_commands = self.version.render_lines(
            "control.async_while.loop_body",
            selectorId=selector_id,
            schedulePath=schedule_context.mcfunction_name,
        )
        loop_commands = add_comment(loop_commands, f"Async While Loop (initialize loop repetition - {context.mcfunction_name !r}):")
        self.add_commands(loop_context.mcfunction_name, loop_commands)
        schedule_cmd = self.version.render(
            "control.async_while.schedule",
            selectorId=selector_id,
            selectorPath=selector_context.mcfunction_name,
        )
        schedule_cmd = add_comment(schedule_cmd, f"Async While Loop (Scheduler - {context.mcfunction_name !r}):")
        self.add_command(schedule_context.mcfunction_name, schedule_cmd)
        selector_commands = self.version.render_lines(
            "control.async_while.selector",
            selectorId=selector_id,
            conditionPath=condition_context.mcfunction_name,
        )
        selector_commands = add_comment(selector_commands, f"Async While Loop (Entity selection - {context.mcfunction_name !r}):")
        self.add_commands(selector_context.mcfunction_name, selector_commands)
        return out
    def visit_MultilineCodeNode(self, node, context: CompileContext) -> CompileResult:
        for statement in node.get_nodes():
            return_value: CompileResult = self.visit(statement, context)
            if return_value.get_return() is not None:
                return return_value
        return CompileResult(MCSNull(context))
    def visit_CodeBlockNode(self, node, context: CompileContext) -> CompileResult:
        local_context = CompileContext(parent=context)
        return_value: CompileResult = self.visit(node.get_body(), local_context)
        commands = self.version.render_lines(
            "control.code_block",
            childStorage=f"mcs_{local_context.uuid}",
            parentStorage=f"mcs_{context.uuid}",
            blockPath=local_context.mcfunction_name,
        )
        commands = add_comment(commands, f"Code block (parent: {context.mcfunction_name !r})")
        self.add_commands(context.mcfunction_name, commands)
        return return_value
    def visit_FunctionCallNode(self, node, context: CompileContext) -> CompileResult:
        fnc: MCSFunction = self.visit(node.get_root(), context).get_value()
        arguments: tuple[mcs_type, ...] = tuple(map(lambda x: self.visit(x, context).get_value(), node.get_arguments()))
        commands, return_value = fnc.call(self, arguments, context)
        is_builtin = ( 
            hasattr(fnc.call, "__module__") and 
            fnc.call.__module__.endswith(".builtin_functions")
        )
        if is_builtin:
            self.used_builtin_functions.add(fnc.call.__name__)
        if commands is not None:
            commands = add_comment(tuple(commands), "Function call")
            self.add_commands(context.mcfunction_name, commands)
        return CompileResult(return_value)
    def visit_EntitySelectorNode(self, node, context: CompileContext) -> CompileResult:
        selector: str = node.get_selector()
        local_context = CompileContext(parent=context)
        out: CompileResult = self.visit(node.get_statement(), local_context)
        setup_commands = self.version.render_lines(
            "control.entity_selector",
            childStorage=f"mcs_{local_context.uuid}",
            parentStorage=f"mcs_{context.uuid}",
            selector=selector,
            childPath=local_context.mcfunction_name,
        )
        commands = add_comment(setup_commands, f"Entity selector {selector !r}")
        self.add_commands(context.mcfunction_name, commands)
        return out if out.get_return() is not None else CompileResult()
    def visit_BinaryOperationNode(self, node, context: CompileContext) -> CompileResult:
        left_value: mcs_type = self.visit(node.get_left_node(), context).get_value()
        right_value: mcs_type = self.visit(node.get_right_node(), context).get_value()
        operation: str = node.get_operator().variant.lower()
        result: mcs_type = MCSNumber(context)
        self.used_math_builtins.add(operation)
        commands = self.version.render_lines(
            "math.binary",
            leftStorage=left_value.get_storage(),
            leftNbt=left_value.get_nbt(),
            rightStorage=right_value.get_storage(),
            rightNbt=right_value.get_nbt(),
            operation=operation,
            resultStorage=f"mcs_{context.uuid}",
            resultNbt=result.get_nbt(),
        )
        commands = add_comment(commands, f"Binary Operation {operation !r}")
        self.add_commands(context.mcfunction_name, commands)
        return CompileResult(result)
    def visit_UnaryOperationNode(self, node, context: CompileContext) -> CompileResult:
        operation = f"u_{node.get_operator()}"
        root: mcs_type = self.visit(node.get_root(), context).get_value()
        result = MCSBoolean(context)
        self.used_math_builtins.add(operation)
        commands = self.version.render_lines(
            "math.unary",
            rootStorage=root.get_storage(),
            rootNbt=root.get_nbt(),
            operation=operation,
            resultStorage=result.get_storage(),
            resultNbt=result.get_nbt(),
        )
        commands = add_comment(commands, f"Unary Operation {operation !r}")
        self.add_commands(context.mcfunction_name, commands)
        return CompileResult(result)
    @staticmethod
    def visit_unknown(node, context):
        raise ValueError(f'Unknown node {node !r}')
    def __repr__(self) -> str:
        return "CompileInterpreter()"

def mcs_compile(ast, functions_dir: str, datapack_id):
    return _mcs_compile(ast, functions_dir, datapack_id)


def _mcs_compile(ast, functions_dir: str, datapack_id):
    context = CompileContext('init', top_level=True)
    interpreter = CompileInterpreter(datapack_id)
    interpreter.visit(ast, context)
    for mcs_fnc in interpreter.functions_to_generate:
        mcs_fnc.generate_function(interpreter)
    version = get_version_context()
    for context_id in interpreter.used_context_ids:
        commands = []
        for compartment in ("current", "variable", "number", "string", "list", "boolean", "unknown", "text_component"):
            commands.append(version.render(
                "kill.remove_compartment",
                ctxStorage=f"mcs_{context_id}",
                compartment=compartment,
            ))
        commands.append("")
        interpreter.add_commands('user_functions/kill', commands)
    for fnc_name in interpreter.get_mcs_functions():
        mcfunction_path = f"{functions_dir}/{fnc_name}.mcfunction"
        Path(mcfunction_path).parent.mkdir(parents=True, exist_ok=True)
        with open(mcfunction_path, "xt") as mcfunction_file:
            mcfunction_file.write(interpreter.get_file_content(fnc_name))
    return interpreter.used_math_builtins, interpreter.used_builtin_functions, interpreter.get_scoreboard_event_hooks()
