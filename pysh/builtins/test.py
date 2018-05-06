import sys
import enum
from typing import Iterable, List, Tuple, Dict, Union

from pysh.builtins import InvokeInfo


class TokenType(enum.Enum):
    Unknown = -2
    EOL = -1
    Value = 0
    LeftParen = 1
    RightParen = 2
    Not = 3
    And = 4
    Or = 5
    StrEqual = 6
    StrNotEqual = 7
    IntEqual = 8
    IntNotEqual = 9
    LessThan = 10
    GreaterThan = 11
    LessThanOrEqual = 12
    GreaterThanOrEqual = 13


class Token(object):
    def __init__(self, raw: str, type: TokenType) -> None:
        self.raw = raw
        self.type = type


class Node(object):
    def accept(self, visitor: 'NodeVisitor') -> None:
        pass


class ValueNode(Node):
    def __init__(self, value: str) -> None:
        self.value = value

    def accept(self, visitor: 'NodeVisitor') -> None:
        visitor.visit_value(self)


class BinaryExpressionNode(Node):
    def __init__(self, lhs: Node, rhs: Node, op: TokenType) -> None:
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

    def accept(self, visitor: 'NodeVisitor') -> None:
        visitor.visit_binary_expression(self)


class NodeVisitor(object):
    def visit_value(self, node: ValueNode) -> None:
        pass

    def visit_binary_expression(self, node: BinaryExpressionNode) -> None:
        pass


class EvaluationError(Exception):
    pass


class EvaluateVisitor(NodeVisitor):
    def __init__(self) -> None:
        self.value: Union[str, bool] = ''
        self.is_boolean = False

    def visit_value(self, node: ValueNode) -> None:
        self.value = node.value
        self.is_boolean = False

    def visit_binary_expression(self, node: BinaryExpressionNode) -> None:
        self.is_boolean = True
        left_visitor = EvaluateVisitor()
        right_visitor = EvaluateVisitor()
        node.lhs.accept(left_visitor)
        node.rhs.accept(right_visitor)

        if left_visitor.is_boolean is not right_visitor.is_boolean:
            raise EvaluationError('Type mismatch')

        if left_visitor.is_boolean:
            raise EvaluationError('Unknown boolean operator ' + node.op.raw)
        else:
            left_value: str = left_visitor.value
            right_value: str = right_visitor.value
            if node.op is TokenType.StrEqual:
                self.value = left_visitor.value == right_visitor.value
            elif node.op is TokenType.StrNotEqual:
                self.value = node.lhs != node.rhs
            elif node.op is TokenType.IntEqual:
                self.value = self.to_int(left_value) == self.to_int(right_value)
            elif node.op is TokenType.IntNotEqual:
                self.value = self.to_int(left_value) != self.to_int(right_value)
            elif node.op is TokenType.LessThan:
                self.value = self.to_int(left_value) < self.to_int(right_value)
            elif node.op is TokenType.GreaterThan:
                self.value = self.to_int(left_value) > self.to_int(right_value)
            elif node.op is TokenType.LessThanOrEqual:
                self.value = self.to_int(left_value) <= self.to_int(right_value)
            elif node.op is TokenType.GreaterThanOrEqual:
                self.value = self.to_int(left_value) >= self.to_int(right_value)
            else:
                raise EvaluationError('Unknown value operator ' + node.op.raw)

    def to_int(self, val: str) -> int:
        try:
            return int(val)
        except ValueError as e:
            # TODO: This should be a specialized exception
            raise EvaluationError('{0}: integer expression expected') from e


def lex_arg(arg: str) -> Token:
    if arg == '(':
        return Token(arg, TokenType.LeftParen)
    if arg == ')':
        return Token(arg, TokenType.RightParen)
    if arg == '!':
        return Token(arg, TokenType.Not)
    if arg == '-a':
        return Token(arg, TokenType.And)
    if arg == '-o':
        return Token(arg, TokenType.Or)
    if arg == '=' or arg == '==':
        return Token(arg, TokenType.StrEqual)
    if arg == '!=':
        return Token(arg, TokenType.StrNotEqual)
    if arg == '-eq':
        return Token(arg, TokenType.IntEqual)
    if arg == '-ne':
        return Token(arg, TokenType.IntNotEqual)
    if arg == '-lt':
        return Token(arg, TokenType.LessThan)
    if arg == '-gt':
        return Token(arg, TokenType.GreaterThan)
    if arg == '-le':
        return Token(arg, TokenType.LessThanOrEqual)
    if arg == '-ge':
        return Token(arg, TokenType.GreaterThanOrEqual)

    return Token(arg, TokenType.Value)


def lex(args: Iterable[str]) -> List[Token]:
    tokens: List[Token] = []
    for arg in args:
        tokens.append(lex_arg(arg))
    tokens.append(Token('', TokenType.EOL))
    return tokens


token_precedences: Dict[TokenType, int] = {
    TokenType.Unknown: -3,
    TokenType.EOL: -2,
    TokenType.Value: -1,
    TokenType.LeftParen: 100,
    TokenType.RightParen: 200,
    TokenType.Not: 300,
    TokenType.And: 400,
    TokenType.Or: 500,
    TokenType.StrEqual: 600,
    TokenType.StrNotEqual: 700,
    TokenType.IntEqual: 800,
    TokenType.IntNotEqual: 900,
    TokenType.LessThan: 1000,
    TokenType.GreaterThan: 1100,
    TokenType.LessThanOrEqual: 1200,
    TokenType.GreaterThanOrEqual: 1300
}


def get_token_precedence(token: Token) -> int:
    return token_precedences.get(token.type, 0)


def parse_value(tokens: List[Token]) -> Tuple[Node, int]:
    return ValueNode(tokens[0].raw), 1


def parse_primary(tokens: List[Token]) -> Tuple[Node, int]:
    return parse_value(tokens)


def parse_bin_op_rhs(tokens: List[Token], precedence: int, lhs: Node) -> Tuple[Node, int]:
    token_offset = 0

    while True:
        op_token = tokens[token_offset]
        op_precedence = get_token_precedence(op_token)

        if op_precedence < precedence:
            break

        # Eat op token
        token_offset += 1

        # Parse rhs
        rhs, consumed = parse_primary(tokens[token_offset:])
        token_offset += consumed

        next_precedence = get_token_precedence(tokens[token_offset])
        if op_precedence < next_precedence:
            rhs, consumed = parse_bin_op_rhs(tokens[token_offset:], op_precedence + 1, lhs)
            token_offset += consumed

        lhs = BinaryExpressionNode(lhs, rhs, op_token.type)

    return lhs, token_offset


def parse(tokens: List[Token]) -> Node:
    lhs, token_offset = parse_primary(tokens)
    node, consumed = parse_bin_op_rhs(tokens[token_offset:], 0, lhs)
    token_offset += consumed

    if tokens[token_offset].type is not TokenType.EOL:
        raise EvaluationError('Too many arguments')

    return node


def test(info: InvokeInfo) -> int:
    if len(info.arguments) < 2:
        return 1

    try:
        tokens = lex(info.arguments[1:])
        node = parse(tokens)
        visitor = EvaluateVisitor()
        node.accept(visitor)
        return_value = 0 if visitor.value else 1
    except EvaluationError as e:
        sys.stderr.write(str(e) + '\n')
        return 2
    return return_value
