from typing import List, Iterable, Optional
from pysh.lexer import Token, TokenType, SymbolToken, ReplacementToken
from pysh.syntaxnodes import SyntaxNode, ArgumentNode, ArgumentPartNode, ArgumentPartType, ExpressionNode


class ParseError(Exception):
    def __init__(self, *args):
        super(__class__, self).__init__(*args)


class StateTickResult(object):
    def __init__(self, *, is_done: bool, child_state: Optional['ParserState'] = None) -> None:
        self.is_done = is_done
        self.child_state = child_state


class ParserState(object):
    def tick(self, token: Token, next_token: Token) -> StateTickResult:
        return StateTickResult(is_done=True)

    @property
    def nodes(self) -> Iterable[SyntaxNode]:
        return []


class WhitespaceState(ParserState):
    def tick(self, token: Token, next_token: Token) -> StateTickResult:
        is_done = next_token.type is not TokenType.WHITESPACE
        return StateTickResult(is_done=is_done)


class ExpressionState(ParserState):
    def __init__(self):
        self.args: List[ArgumentNode] = []
        self.arg_parts: List[ArgumentPartNode] = []
        self.is_inside_quotes = False

    def tick(self, token: Token, next_token: Token) -> StateTickResult:
        if token.type is TokenType.WHITESPACE:
            if self.is_inside_quotes:
                token: SymbolToken = token
                # TODO: store whitespace value with whitespace token
                part_node = ArgumentPartNode(ArgumentPartType.CONSTANT, ' ')
                self.arg_parts.append(part_node)
            else:
                self.finish_arg()
            return StateTickResult(is_done=False)

        if token.type is TokenType.EOS:
            if self.is_inside_quotes:
                raise ParseError('Unexpected end of string. Expecting end of quotes.')
            else:
                self.finish_arg()
            return StateTickResult(is_done=True)

        if token.type is TokenType.QUOTES:
            self.is_inside_quotes = not self.is_inside_quotes
            return StateTickResult(is_done=False)

        if token.type is TokenType.SYMBOL:
            token: SymbolToken = token
            part_node = ArgumentPartNode(ArgumentPartType.CONSTANT, token.value)
            self.arg_parts.append(part_node)
            return StateTickResult(is_done=False)

        if token.type is TokenType.REPLACEMENT:
            token: ReplacementToken = token
            type = ArgumentPartType.REPLACEMENT_SINGLE if self.is_inside_quotes else ArgumentPartType.REPLACEMENT
            part_node = ArgumentPartNode(type, token.value)
            self.arg_parts.append(part_node)
            return StateTickResult(is_done=False)

        raise ParseError('Unexpected token while parsing expression: ' + str(token.type))

    def finish_arg(self) -> None:
        if len(self.arg_parts) > 0:
            arg_node = ArgumentNode()
            arg_node.parts = self.arg_parts
            self.arg_parts = []
            self.args.append(arg_node)

    @property
    def nodes(self) -> Iterable[SyntaxNode]:
        return [ExpressionNode(self.args)]


class Parser(object):
    def __init__(self) -> None:
        self.syntax: List[SyntaxNode] = []
        self.tokens: List[Token] = []
        self.state: Optional[ParserState] = None
        self.state_stack: List[ParserState] = []
        self.nodes: List[SyntaxNode] = []

    def parse(self, tokens: List[Token]) -> List[SyntaxNode]:
        self.nodes = []
        self.tokens = tokens

        while len(self.tokens) > 0:
            self.process_token(self.pop_token())

        return self.nodes

    def process_token(self, token: Token) -> None:
        if self.state is None:
            self.state = self.get_next_state(token)

        result = self.state.tick(token, self.peek_token())
        if result.child_state is not None:
            if not result.is_done:
                self.state_stack.append(self.state)
        if result.is_done:
            if len(self.state_stack) > 0:
                self.state = self.state_stack.pop()
            else:
                self.nodes.extend(self.state.nodes)
                self.state = None

    def get_next_state(self, token: Token) -> ParserState:
        type = token.type
        if type == TokenType.WHITESPACE or type == TokenType.EOS:
            return WhitespaceState()
        elif type == TokenType.SYMBOL or type == TokenType.REPLACEMENT:
            return ExpressionState()

        raise ParseError('Unexpected token ' + str(type))

    def peek_token(self) -> Token:
        if len(self.tokens) > 0:
            return self.tokens[0]
        return Token()

    def pop_token(self) -> Token:
        # TODO: This sucks performance wise
        token = self.tokens[0]
        self.tokens = self.tokens[1:]
        return token

    @property
    def is_done(self) -> bool:
        return self.state is None and len(self.state_stack) is 0
