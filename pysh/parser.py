from typing import List, Iterable, Optional
from pysh.lexer import Token, TokenType, SymbolToken, ReplacementToken
from pysh.syntaxnodes import SyntaxNode, ArgumentNode, ArgumentPartNode, ArgumentPartType, CommandNode, \
    AssignmentNode


class ParseError(Exception):
    def __init__(self, *args):
        super(__class__, self).__init__(*args)


class StateTickResult(object):
    def __init__(self, *, is_done: bool, tokens_to_eat: int = 0, child_state: Optional['ParserState'] = None) -> None:
        self.is_done = is_done
        self.tokens_to_eat = tokens_to_eat
        self.child_state = child_state


class ParserState(object):
    def tick(self, tokens: List[Token]) -> StateTickResult:
        return StateTickResult(is_done=True, tokens_to_eat=0)

    @property
    def nodes(self) -> Iterable[SyntaxNode]:
        return []


class TopLevelExpressionState(ParserState):
    def __init__(self) -> None:
        self.child_state: Optional[ParserState] = None

    def tick(self, tokens: List[Token]) -> StateTickResult:
        if self.child_state is not None:
            return StateTickResult(is_done=True, tokens_to_eat=0)

        type = tokens[0].type

        if type is TokenType.WHITESPACE or type is TokenType.EOS:
            return self.enter_child(WhitespaceState())
        elif type is TokenType.SYMBOL or type is TokenType.REPLACEMENT:
            return self.enter_child(ExpressionState())

        raise ParseError('Unexpected token ' + str(type))

    def enter_child(self, child_state: ParserState) -> StateTickResult:
        self.child_state = child_state
        return StateTickResult(is_done=False, tokens_to_eat=0, child_state=child_state)

    @property
    def nodes(self):
        return self.child_state.nodes


class WhitespaceState(ParserState):
    def tick(self, tokens: List[Token]) -> StateTickResult:
        if len(tokens) is 0:
            return StateTickResult(is_done=True, tokens_to_eat=0)
        token = tokens[0]
        if token.type is TokenType.WHITESPACE or token.type is TokenType.EOS:
            return StateTickResult(is_done=False, tokens_to_eat=1)
        else:
            return StateTickResult(is_done=True, tokens_to_eat=0)


class ArgumentState(ParserState):
    def __init__(self):
        self.arg_parts: List[ArgumentPartNode] = []
        self.is_inside_quotes = False

    def tick(self, tokens: List[Token]) -> StateTickResult:
        if len(tokens) < 2:
            return StateTickResult(is_done=False, tokens_to_eat=0)
        token = tokens[0]
        next_token = tokens[1].type

        if token.type is TokenType.WHITESPACE and self.is_inside_quotes:
            if self.is_inside_quotes:
                token: SymbolToken = token
                # TODO: store whitespace value with whitespace token
                part_node = ArgumentPartNode(ArgumentPartType.CONSTANT, ' ')
                self.arg_parts.append(part_node)

        elif token.type is TokenType.QUOTES:
            self.is_inside_quotes = not self.is_inside_quotes

        elif token.type is TokenType.SYMBOL:
            token: SymbolToken = token
            part_node = ArgumentPartNode(ArgumentPartType.CONSTANT, token.value)
            self.arg_parts.append(part_node)

        elif token.type is TokenType.REPLACEMENT:
            token: ReplacementToken = token
            type = ArgumentPartType.REPLACEMENT_SINGLE if self.is_inside_quotes else ArgumentPartType.REPLACEMENT
            part_node = ArgumentPartNode(type, token.value)
            self.arg_parts.append(part_node)

        else:
            raise ParseError('Unexpected token while parsing expression: ' + str(token.type))

        is_done = False
        if next_token is TokenType.WHITESPACE and not self.is_inside_quotes:
            is_done = True
        if next_token is TokenType.EOS:
            if self.is_inside_quotes:
                raise ParseError('Unexpected end of string. Expecting end of quotes.')
            else:
                is_done = True

        return StateTickResult(is_done=is_done, tokens_to_eat=1)

    @property
    def nodes(self) -> Iterable[SyntaxNode]:
        return [self.make_argument_node()]

    def make_argument_node(self) -> ArgumentNode:
        arg_node = ArgumentNode()
        arg_node.parts = self.arg_parts
        self.arg_parts = []
        return arg_node


class ExpressionState(ParserState):
    def __init__(self) -> None:
        self.assignments: List[AssignmentNode] = []
        self.assignment_state: Optional[AssignmentState] = None
        self.command_state: Optional[CommandState] = None
        self.finished_assignments = False

    def tick(self, tokens: List[Token]) -> StateTickResult:
        if self.assignment_state is not None:
            # We have returned from parsing an env assignment.
            self.assignments.append(self.assignment_state.make_assignment_node())
            self.assignment_state = None

        if self.command_state is not None:
            return StateTickResult(is_done=True, tokens_to_eat=0)

        token = tokens[0]

        # Eat whitespace
        if token.type == TokenType.WHITESPACE:
            return StateTickResult(is_done=False, tokens_to_eat=1)

        if token.type == TokenType.EOS:
            return StateTickResult(is_done=True, tokens_to_eat=1)

        if not self.finished_assignments:
            if len(tokens) < 2:
                return StateTickResult(is_done=False, tokens_to_eat=0)
            if tokens[0].type == TokenType.SYMBOL and tokens[1].type == TokenType.ASSIGNMENT:
                self.assignment_state = AssignmentState()
                return StateTickResult(is_done=False, tokens_to_eat=0, child_state=self.assignment_state)
            self.finished_assignments = True

        self.command_state = CommandState()
        return StateTickResult(is_done=False, tokens_to_eat=0, child_state=self.command_state)

    @property
    def nodes(self) -> Iterable[SyntaxNode]:
        nodes = []
        if self.command_state is not None and len(self.command_state.argument_nodes) > 0:
            # We are invoking a command, not assigning variables.
            nodes.append(CommandNode(self.command_state.argument_nodes, self.assignments))
        else:
            # We are making variable assignments.
            nodes.extend(self.assignments)
        return nodes


class CommandState(ParserState):
    def __init__(self) -> None:
        self.args: List[ArgumentNode] = []
        self.arg_state: Optional[ArgumentState] = None

    def tick(self, tokens: List[Token]) -> StateTickResult:
        if self.arg_state is not None:
            self.args.append(self.arg_state.make_argument_node())
            self.arg_state = None

        token = tokens[0]

        if token.type == TokenType.WHITESPACE:
            return StateTickResult(is_done=False, tokens_to_eat=1)

        if token.type == TokenType.EOS:
            return StateTickResult(is_done=True, tokens_to_eat=1)

        self.arg_state = ArgumentState()
        return StateTickResult(is_done=False, tokens_to_eat=0, child_state=self.arg_state)

    @property
    def nodes(self) -> Iterable[SyntaxNode]:
        return []

    @property
    def argument_nodes(self):
        return self.args


class AssignmentState(ParserState):
    def __init__(self) -> None:
        self.lhs_var_name: Optional[str] = None
        self.rhs_arg_state: Optional[ArgumentState] = None

    def tick(self, tokens: List[Token]) -> StateTickResult:
        if self.lhs_var_name is None:
            # Eat symbol and assignment operator
            token: SymbolToken = tokens[0]
            self.lhs_var_name = token.value
            return StateTickResult(is_done=False, tokens_to_eat=2)

        if self.rhs_arg_state is None:
            self.rhs_arg_state = ArgumentState()
            return StateTickResult(is_done=False, tokens_to_eat=0, child_state=self.rhs_arg_state)

        return StateTickResult(is_done=True, tokens_to_eat=0)

    @property
    def nodes(self) -> Iterable[SyntaxNode]:
        return [self.make_assignment_node()]

    def make_assignment_node(self) -> AssignmentNode:
        return AssignmentNode(self.lhs_var_name, self.rhs_arg_state.make_argument_node())


class Parser(object):
    def __init__(self) -> None:
        self.syntax: List[SyntaxNode] = []
        self.tokens: List[Token] = []
        self.state: Optional[ParserState] = None
        self.state_stack: List[ParserState] = []
        self.nodes: List[SyntaxNode] = []

    def parse(self, tokens: List[Token]) -> List[SyntaxNode]:
        self.tokens = tokens
        self.process_tokens()
        result_nodes = self.nodes
        self.nodes = []
        return result_nodes

    def process_tokens(self) -> None:
        self.state = TopLevelExpressionState()
        while len(self.tokens) > 0 or self.state is not None:
            if self.state is None:
                self.state = TopLevelExpressionState()

            result = self.state.tick(self.tokens)
            del self.tokens[:result.tokens_to_eat]
            if result.child_state is not None:
                if not result.is_done:
                    self.state_stack.append(self.state)
                    self.state = result.child_state
            if result.is_done:
                if len(self.state_stack) > 0:
                    self.state = self.state_stack.pop()
                else:
                    self.nodes.extend(self.state.nodes)
                    self.state = None

    def pop_token(self) -> Token:
        # TODO: This sucks performance wise
        token = self.tokens[0]
        self.tokens = self.tokens[1:]
        return token

    @property
    def is_done(self) -> bool:
        return self.state is None and len(self.state_stack) is 0
