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
    parser.add_argument('--stdinline', action='append')
    return parser


class Interactive(object):
    def __init__(self) -> None:
        self.is_command = False
        self.lexer = Lexer()
        self.parser = Parser()
        self.generator = CodeGenerator()
        self.interpreter = Interpreter()

    def print_prompt(self) -> None:
        if self.is_command:
            return
        if self.parser.is_done:
            sys.stdout.write('pysh$ ')
        else:
            sys.stdout.write('> ')
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
        if args.stdinline is not None and len(args.stdinline) > 0:
            input_source = []
            for line in args.stdinline:
                input_source.append(line + '\n')
        if args.command:
            input_source = [args.command]
            self.is_command = True

        install_builtins(self.interpreter)

        def tick(source: str) -> None:
            ast: Optional[List[SyntaxNode]] = None

            tokens = self.lexer.lex_all(source)
            if mode is InteractiveMode.Lex:
                print(repr(tokens))
                return

            try:
                ast = self.parser.parse(tokens)
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

            code = self.generator.generate(ast)
            if mode is InteractiveMode.GenerateCode:
                if code is not None:
                    self.print_code(code)
                return

            if code is not None:
                self.interpreter.execute(code)

        # Interactive
        if not self.is_command:
            self.print_prompt()
            for line in input_source:
                tick(line)
                self.print_prompt()
            return 0

        # Single command
        tick(args.command + '\n')
        return 0
