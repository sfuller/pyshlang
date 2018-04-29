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

    def __repr__(self) -> str:
        return '<ArgumentPartNode type: {0}, value: {1}>'.format(repr(self.type), repr(self.value))

    def accept(self, visitor: 'SyntaxNodeVisitor') -> None:
        visitor.visit_argument_part_node(self)


class ArgumentNode(SyntaxNode):
    def __init__(self) -> None:
        self.parts: List[ArgumentPartNode] = []

    def __repr__(self) -> str:
        return '<ArgumentNode parts: {0}>'.format(repr(self.parts))

    def accept(self, visitor: 'SyntaxNodeVisitor') -> None:
        visitor.visit_argument_node(self)


class ExpressionNode(SyntaxNode):
    def __init__(self, args: List[ArgumentNode]) -> None:
        self.args = args

    def __repr__(self) -> str:
        return '<ExpressionNode args: {0}>'.format(repr(self.args))

    def accept(self, visitor: 'SyntaxNodeVisitor') -> None:
        visitor.visit_expression_node(self)


class SyntaxNodeVisitor(object):
    def visit_argument_part_node(self, node: ArgumentPartNode) -> None:
        pass

    def visit_argument_node(self, node: ArgumentNode) -> None:
        pass

    def visit_expression_node(self, node: ExpressionNode) -> None:
        pass
