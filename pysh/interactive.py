import argparse
import enum
import sys
from typing import Optional, List, Iterable

from pysh.codegen import CodeGenerator, Instruction
from pysh.il import GenerateILVisitor
from pysh.interpreter import Interpreter
from pysh.lexer import Lexer
from pysh.parser import Parser, ParseError
from pysh.syntaxnodes import SyntaxNode


class InteractiveMode(enum.Enum):
    Execute = 0
    GenerateCode = 1
    Parse = 2
    Lex = 3


def print_prompt() -> None:
    sys.stdout.write('pysh$ ')
    sys.stdout.flush()


def print_code(code: Iterable[Instruction]) -> None:
    visitor = GenerateILVisitor()
    for instruction in code:
        instruction.accept(visitor)
    print(visitor.make_il())


def make_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('execute', 'codegen', 'parse', 'lex'), default='execute')
    return parser


def main() -> int:
    parser = make_argparser()
    args = parser.parse_args()
    mode = InteractiveMode.Execute
    if args.mode == 'execute':
        mode = InteractiveMode.Execute
    elif args.mode == 'codegen':
        mode = InteractiveMode.GenerateCode
    elif args.mode == 'parse':
        mode = InteractiveMode.Parse
    elif args.mode == 'lex':
        mode = InteractiveMode.Lex

    lexer = Lexer()
    parser = Parser()
    generator = CodeGenerator()
    interpreter = Interpreter()

    print_prompt()

    for line in sys.stdin:
        line = line + '\n'

        ast: Optional[List[SyntaxNode]] = None
        code: Optional[List[Instruction]] = None

        tokens = lexer.lex_all(line)

        try:
            ast = parser.parse(tokens)
        except ParseError as e:
            sys.stderr.write(str(e))
            sys.stderr.write('\n')

        if ast is not None:
            code = generator.generate(ast)

        if mode is InteractiveMode.Execute:
            if code is not None:
                interpreter.execute(code)
        elif mode is InteractiveMode.GenerateCode:
            if code is not None:
                print_code(code)
        elif mode is InteractiveMode.Parse:
            if ast is not None:
                print(repr(ast))
        elif mode is InteractiveMode.Lex:
            print(repr(tokens))

        print_prompt()

    return 0
