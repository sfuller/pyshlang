import enum
from typing import List


class SyntaxNode(object):
    def accept(self, visitor: 'SyntaxNodeVisitor') -> None:
        pass


class ArgumentPartType(enum.Enum):
    CONSTANT = 0
    REPLACEMENT = 1
    REPLACEMENT_SINGLE = 2


class ArgumentPartNode(SyntaxNode):
    def __init__(self, type: ArgumentPartType, value: str) -> None:
        self.type = type
        self.value = value

    def accept(self, visitor: 'SyntaxNodeVisitor') -> None:
        visitor.visit_argument_part_node(self)


class ArgumentNode(SyntaxNode):
    def __init__(self) -> None:
        self.parts: List[ArgumentPartNode] = []

    def accept(self, visitor: 'SyntaxNodeVisitor') -> None:
        visitor.visit_argument_node(self)


class AssignmentNode(SyntaxNode):
    def __init__(self, var_name: str, expr: ArgumentNode) -> None:
        self.var_name = var_name
        self.expr = expr

    def accept(self, visitor: 'SyntaxNodeVisitor') -> None:
        visitor.visit_assignment_node(self)


class CommandNode(SyntaxNode):
    def __init__(self, args: List[ArgumentNode], env_assignments: List[AssignmentNode]) -> None:
        self.args = args
        self.env_assignments = env_assignments

    def accept(self, visitor: 'SyntaxNodeVisitor') -> None:
        visitor.visit_command_node(self)


class SyntaxNodeVisitor(object):
    def visit_argument_part_node(self, node: ArgumentPartNode) -> None:
        pass

    def visit_argument_node(self, node: ArgumentNode) -> None:
        pass

    def visit_command_node(self, node: CommandNode) -> None:
        pass

    def visit_assignment_node(self, node: AssignmentNode) -> None:
        pass
