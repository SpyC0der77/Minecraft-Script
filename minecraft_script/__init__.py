from .lexer.lexer import Lexer
from .parser.parser import Parser
from .interpreter.interpreter import Interpreter, InterpreterContext, SymbolTable
from .imports import parse_code_with_imports


def debug_code(
    code_input: str,
    *,
    print_variables: bool = False,
    source_path=None,
    import_base_dir=None,
) -> None:
    interpreter = Interpreter()
    context = InterpreterContext(top_level=True)
    interpreter.visit(parse_code(code_input, source_path=source_path, import_base_dir=import_base_dir), context)

    if print_variables:
        print(context.symbol_table.symbols)

    print("\n\nCode ended with no errors.")


def run_shell():
    context = InterpreterContext(top_level=True)

    while True:
        text = input('> ')
        while text.strip(' ') == '':
            text = input('> ')

        run_lexer = Lexer(text)
        tokens = run_lexer.tokenize()

        run_parser = Parser(tokens)
        ast = run_parser.parse()

        run_interpreter = Interpreter()
        print(run_interpreter.visit(ast, context))


def parse_code(code: str, *, source_path=None, import_base_dir=None):
    return parse_code_with_imports(code, source_path=source_path, import_base_dir=import_base_dir)
