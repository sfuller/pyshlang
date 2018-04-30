import argparse
import enum
import sys
from typing import Optional, List, Iterable

from pysh.codegen import CodeGenerator, Instruction
from pysh.il import GenerateILVisitor
from pysh.interpreter import Interpreter, install_builtins
from pysh.lexer import Lexer
from pysh.parser import Parser, ParseError
from pysh.syntaxnoderepr import SyntaxNodeReprVisitor
from pysh.syntaxnodes import SyntaxNode


class InteractiveMode(enum.Enum):
    Execute = 0
    GenerateCode = 1
    Parse = 2
    Lex = 3


def make_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('execute', 'codegen', 'parse', 'lex'), default='execute')
    parser.add_argument('-c', '--command', dest='command')
    return parser


class Interactive(object):
    def __init__(self) -> None:
        self.is_command = False

    def print_prompt(self) -> None:
        if self.is_command:
            return
        sys.stdout.write('pysh$ ')
        sys.stdout.flush()

    def print_code(self, code: Iterable[Instruction]) -> None:
        visitor = GenerateILVisitor()
        for instruction in code:
            instruction.accept(visitor)
        print(visitor.make_il())

    def main(self) -> int:
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

        input_source = sys.stdin
        if args.command:
            input_source = [args.command]
            self.is_command = True

        lexer = Lexer()
        parser = Parser()
        generator = CodeGenerator()
        interpreter = Interpreter()

        install_builtins(interpreter)

        self.print_prompt()

        for line in input_source:
            line = line + '\n'

            def tick() -> None:
                ast: Optional[List[SyntaxNode]] = None
                code: Optional[List[Instruction]] = None

                tokens = lexer.lex_all(line)
                if mode is InteractiveMode.Lex:
                    print(repr(tokens))
                    return

                try:
                    ast = parser.parse(tokens)
                except ParseError as e:
                    sys.stderr.write(str(e))
                    sys.stderr.write('\n')
                if mode is InteractiveMode.Parse:
                    if ast is not None:
                        visitor = SyntaxNodeReprVisitor()
                        for node in ast:
                            node.accept(visitor)
                        print(str(visitor))
                    return

                if ast is None:
                    return

                code = generator.generate(ast)
                if mode is InteractiveMode.GenerateCode:
                    if code is not None:
                        self.print_code(code)
                    return

                if code is not None:
                    interpreter.execute(code)

            tick()
            self.print_prompt()

        return 0
