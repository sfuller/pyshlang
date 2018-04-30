from typing import List, Iterable

from pysh.syntaxnodes import SyntaxNodeVisitor, ArgumentPartNode, ArgumentNode, CommandNode, AssignmentNode, SyntaxNode


class SyntaxNodeReprVisitor(SyntaxNodeVisitor):
    def __init__(self) -> None:
        self.parts: List[str] = []
        self.indent_level = 0

    def visit_argument_part_node(self, node: ArgumentPartNode) -> None:
        self.add_line('Argument Part: type: {0} value: {1}\n'.format(node.type, node.value))

    def visit_argument_node(self, node: ArgumentNode) -> None:
        self.add_line('Argument:\n')
        self.indent_level += 1
        self.add_list('parts', node.parts)
        self.indent_level -= 1

    def visit_command_node(self, node: CommandNode) -> None:
        self.add_line('Command:\n')
        self.indent_level += 1
        self.add_list('env_assignments', node.env_assignments)
        self.add_list('args', node.args)
        self.indent_level -= 1

    def visit_assignment_node(self, node: AssignmentNode) -> None:
        self.add_line('Assignment:\n')
        self.indent_level += 1
        self.add_line('var_name: {0}\n'.format(node.var_name))
        self.add_line('expr: \n')
        self.indent_level += 1
        self.visit_argument_node(node.expr)
        self.indent_level -= 2

    def add_line(self, val: str) -> None:
        for i in range(self.indent_level):
            self.parts.append('  ')
        self.parts.append(val)

    def empty_list(self):
        self.parts.append(': []\n')

    def start_list(self) -> None:
        self.parts.append(': [\n')
        self.indent_level += 1

    def end_list(self) -> None:
        self.indent_level -= 1
        self.add_line(']\n')

    def add_list(self, name: str, nodes: List[SyntaxNode]) -> None:
        self.add_line(name)
        if len(nodes) is 0:
            self.empty_list()
        else:
            self.start_list()
            for node in nodes:
                node.accept(self)
            self.end_list()

    def __str__(self) -> str:
        return ''.join(self.parts)
