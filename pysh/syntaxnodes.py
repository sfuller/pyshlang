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
    def __init__(self) -> None:
        self.var_name: str = ''
        self.expr = ArgumentNode()

    def accept(self, visitor: 'SyntaxNodeVisitor') -> None:
        visitor.visit_assignment_node(self)


class AssignmentsNode(SyntaxNode):
    def __init__(self) -> None:
        self.assignments: List[AssignmentNode] = []

    def accept(self, visitor: 'SyntaxNodeVisitor') -> None:
        visitor.visit_assignments_node(self)


class CommandNode(SyntaxNode):
    def __init__(self) -> None:
        self.args: List[ArgumentNode] = []
        self.env_assignments: List[AssignmentNode] = []

    def accept(self, visitor: 'SyntaxNodeVisitor') -> None:
        visitor.visit_command_node(self)


class ConditionalNode(SyntaxNode):
    def __init__(self) -> None:
        self.evaluation_expressions: List[SyntaxNode] = []
        self.conditional_expressions: List[SyntaxNode] = []
        self.else_expressions: List[SyntaxNode] = []

    def accept(self, visitor: 'SyntaxNodeVisitor') -> None:
        visitor.visit_conditional_node(self)


class SyntaxNodeVisitor(object):
    def visit_argument_part_node(self, node: ArgumentPartNode) -> None:
        raise NotImplementedError()

    def visit_argument_node(self, node: ArgumentNode) -> None:
        raise NotImplementedError()

    def visit_command_node(self, node: CommandNode) -> None:
        raise NotImplementedError()

    def visit_assignment_node(self, node: AssignmentNode) -> None:
        raise NotImplementedError()

    def visit_assignments_node(self, node: AssignmentsNode) -> None:
        raise NotImplementedError()

    def visit_conditional_node(self, node: ConditionalNode) -> None:
        raise NotImplementedError()
