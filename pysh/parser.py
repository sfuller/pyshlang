from typing import List, Optional
from pysh.lexer import Token, TokenType
from pysh.syntaxnodes import SyntaxNode, ArgumentNode, ArgumentPartNode, ArgumentPartType, CommandNode, \
    AssignmentNode, AssignmentsNode, ConditionalNode


class ParseError(Exception):
    def __init__(self, *args):
        super(__class__, self).__init__(*args)


class StateTickResult(object):
    def __init__(self, *, is_done: bool = False, is_incomplete: bool = False, tokens_to_eat: int = 0,
                 child_state: Optional['ParserState'] = None) -> None:
        self.is_done = is_done
        self.is_incomplete = is_incomplete
        self.tokens_to_eat = tokens_to_eat
        self.child_state = child_state


class ParserState(object):
    def tick(self, tokens: List[Token]) -> StateTickResult:
        return StateTickResult(is_done=True, tokens_to_eat=0)

    @property
    def node(self) -> Optional[SyntaxNode]:
        return None


class TopLevelExpressionState(ParserState):
    def __init__(self) -> None:
        self.child_state: Optional[ParserState] = None

    def tick(self, tokens: List[Token]) -> StateTickResult:
        if self.child_state is not None:
            return StateTickResult(is_done=True, tokens_to_eat=0)

        if len(tokens) is 0:
            return StateTickResult(is_done=True)

        token = tokens[0]
        type = token.type

        if type is TokenType.WHITESPACE or type is TokenType.EOS:
            return StateTickResult(is_done=True, tokens_to_eat=1)
        elif type is TokenType.SYMBOL or type is TokenType.DOLLAR_SIGN or type is TokenType.QUOTES:
            return self.enter_child(ExpressionState())
        elif type is TokenType.IF:
            return self.enter_child(ConditionalState())

        raise ParseError('Unexpected token {0} in top level expression'.format(type))

    def enter_child(self, child_state: ParserState) -> StateTickResult:
        self.child_state = child_state
        return StateTickResult(is_done=False, tokens_to_eat=0, child_state=child_state)

    @property
    def node(self) -> Optional[SyntaxNode]:
        if self.child_state is None:
            return None
        return self.child_state.node


class ReplacementState(ParserState):
    def __init__(self) -> None:
        self.has_parsed_prefix = False
        self.has_parsed_key = False
        self.is_block_syntax = False
        self.key_parts: List[str] = []

    def tick(self, tokens: List[Token]) -> StateTickResult:
        if not self.has_parsed_prefix:
            self.has_parsed_prefix = True
            if len(tokens) < 2:
                return StateTickResult(is_incomplete=True)
            if tokens[1].type is TokenType.LEFT_CURLY_BRACKET:
                self.is_block_syntax = True
                return StateTickResult(tokens_to_eat=2)
            return StateTickResult(tokens_to_eat=1)

        if len(tokens) is 0:
            return StateTickResult(is_incomplete=True)

        # Parse inners
        if not self.has_parsed_key:
            token = tokens[0]
            if token.type is TokenType.RIGHT_CURLY_BRACKET:
                if self.is_block_syntax:
                    self.has_parsed_key = True
                    return StateTickResult(tokens_to_eat=0)
                raise ParseError('Unexpected {0}'.format(token.value))

            if token.type is TokenType.SYMBOL:
                self.key_parts.append(token.value)
                return StateTickResult(tokens_to_eat=1)

            self.has_parsed_key = True
            return StateTickResult()

        # Parse ending bracket if applicable
        if self.is_block_syntax:
            token = tokens[0]
            if token.type is not TokenType.RIGHT_CURLY_BRACKET:
                raise ParseError('Expecting }')
            return StateTickResult(is_done=True, tokens_to_eat=1)

        return StateTickResult(is_done=True)

    def get_replacement_key(self) -> str:
        return ''.join(self.key_parts)


class ArgumentState(ParserState):
    def __init__(self) -> None:
        self.arg_parts: List[ArgumentPartNode] = []
        self.is_inside_quotes = False
        self.replacement_state: Optional[ReplacementState] = None
        self.parsed_nodes: List[SyntaxNode] = []
        self._node = ArgumentNode()

    def tick(self, tokens: List[Token]) -> StateTickResult:
        if self.replacement_state is not None:
            type = ArgumentPartType.REPLACEMENT_SINGLE if self.is_inside_quotes else ArgumentPartType.REPLACEMENT
            self.arg_parts.append(ArgumentPartNode(type, self.replacement_state.get_replacement_key()))
            self.replacement_state = None

        if len(tokens) is 0:
            return StateTickResult(is_incomplete=True)

        token = tokens[0]

        if token.type is TokenType.WHITESPACE or token.type is TokenType.EOS:
            if self.is_inside_quotes:
                part_node = ArgumentPartNode(ArgumentPartType.CONSTANT, token.value)
                self.arg_parts.append(part_node)
                return StateTickResult(tokens_to_eat=1)
            else:
                return self._finish_node()

        if token.type is TokenType.QUOTES:
            self.is_inside_quotes = not self.is_inside_quotes
            return StateTickResult(tokens_to_eat=1)

        if token.type is TokenType.SYMBOL:
            part_node = ArgumentPartNode(ArgumentPartType.CONSTANT, token.value)
            self.arg_parts.append(part_node)
            return StateTickResult(tokens_to_eat=1)

        if token.type is TokenType.DOLLAR_SIGN:
            self.replacement_state = ReplacementState()
            return StateTickResult(child_state=self.replacement_state)

        raise ParseError('Unexpected token while parsing expression: ' + str(token.type))

    @property
    def node(self) -> SyntaxNode:
        return self._node

    @property
    def argument_node(self) -> ArgumentNode:
        return self._node

    def _finish_node(self) -> StateTickResult:
        self._node.parts = self.arg_parts
        return StateTickResult(is_done=True, tokens_to_eat=0)


class ExpressionState(ParserState):
    def __init__(self) -> None:
        self.assignments: List[AssignmentNode] = []
        self.assignment_state: Optional[AssignmentState] = None
        self.command_state: Optional[CommandState] = None
        self.has_parsed_assignments = False
        self.has_parsed_command = False
        self.command_node: Optional[CommandNode] = None
        self.assignments_node: Optional[AssignmentsNode] = None

    def tick(self, tokens: List[Token]) -> StateTickResult:
        if self.assignment_state is not None:
            # We have returned from parsing an env assignment.
            self.assignments.append(self.assignment_state.assignment_node)
            self.assignment_state = None

        if self.command_state is not None:
            self.has_parsed_command = True

        if len(tokens) is 0:
            return StateTickResult(is_incomplete=True)
        token = tokens[0]

        # Eat whitespace
        if token.type == TokenType.WHITESPACE:
            return StateTickResult(tokens_to_eat=1)

        if token.type == TokenType.EOS:
            # Finish parsing expression
            if self.command_state is not None and len(self.command_state.args) > 0:
                # We are invoking a command, not assigning variables.
                self.command_node = CommandNode()
                self.command_node.args = self.command_state.args
                self.command_node.env_assignments = self.assignments
            else:
                # We are making variable assignments.
                self.assignments_node = AssignmentsNode()
                self.assignments_node.assignments.extend(self.assignments)
            return StateTickResult(is_done=True, tokens_to_eat=1)

        if not self.has_parsed_assignments:
            next_token = None if len(tokens) < 2 else tokens[1]
            if token.type is TokenType.SYMBOL and next_token is not None and next_token.type is TokenType.ASSIGNMENT:
                self.assignment_state = AssignmentState()
                return StateTickResult(child_state=self.assignment_state)
            self.has_parsed_assignments = True

        if not self.has_parsed_command:
            self.command_state = CommandState()
            return StateTickResult(child_state=self.command_state)

    @property
    def node(self) -> SyntaxNode:
        if self.command_node is not None:
            return self.command_node
        if self.assignments_node is not None:
            return self.assignments_node
        return SyntaxNode()


class CommandState(ParserState):
    def __init__(self) -> None:
        self.args: List[ArgumentNode] = []
        self.arg_state: Optional[ArgumentState] = None

    def tick(self, tokens: List[Token]) -> StateTickResult:
        if self.arg_state is not None:
            self.args.append(self.arg_state.argument_node)
            self.arg_state = None

        if len(tokens) is 0:
            return StateTickResult(is_incomplete=True)
        token = tokens[0]

        if token.type == TokenType.WHITESPACE:
            return StateTickResult(tokens_to_eat=1)

        if token.type == TokenType.EOS:
            return StateTickResult(is_done=True, tokens_to_eat=0)

        self.arg_state = ArgumentState()
        return StateTickResult(child_state=self.arg_state)


class AssignmentState(ParserState):
    def __init__(self) -> None:
        self.lhs_var_name: Optional[str] = None
        self.rhs_arg_state: Optional[ArgumentState] = None
        self.parsed_nodes: List[SyntaxNode] = []
        self._node = AssignmentNode()

    def tick(self, tokens: List[Token]) -> StateTickResult:
        if len(tokens) is 0:
            return StateTickResult(is_incomplete=True)

        if self.lhs_var_name is None:
            # Eat symbol and assignment operator
            token = tokens[0]
            self.lhs_var_name = token.value
            return StateTickResult(tokens_to_eat=2)

        if self.rhs_arg_state is None:
            self.rhs_arg_state = ArgumentState()
            return StateTickResult(child_state=self.rhs_arg_state)

        self.node.var_name = self.lhs_var_name
        self.node.expr = self.rhs_arg_state.argument_node
        self.parsed_nodes.append(self.node)
        return StateTickResult(is_done=True, tokens_to_eat=0)

    @property
    def node(self) -> SyntaxNode:
        return self._node

    @property
    def assignment_node(self) -> AssignmentNode:
        return self._node


class ConditionalState(ParserState):
    def __init__(self) -> None:
        self.has_parsed_if = False
        self.has_parsed_conditions = False
        self.has_parsed_then = False
        self.has_parsed_expressions = False
        self.has_parsed_else = False
        self.has_parsed_else_expressions = False
        self.expression_state: Optional[ExpressionState] = None
        self._node = ConditionalNode()

    def tick(self, tokens: List[Token]) -> StateTickResult:
        if len(tokens) is 0:
            return StateTickResult(is_incomplete=True)

        token = tokens[0]

        if token.type is TokenType.WHITESPACE:
            return StateTickResult(tokens_to_eat=1)

        if not self.has_parsed_if:
            self.has_parsed_if = True
            return StateTickResult(tokens_to_eat=1)

        if not self.has_parsed_conditions:
            if self.expression_state is None:
                self.expression_state = ExpressionState()
                return StateTickResult(child_state=self.expression_state)
            else:
                self._node.evaluation_expressions.append(self.expression_state.node)
                self.has_parsed_conditions = True
                self.expression_state = None
                return StateTickResult()

        if not self.has_parsed_then:
            if token.type is not TokenType.THEN:
                self.has_parsed_conditions = False
                return StateTickResult()
            self.has_parsed_then = True
            return StateTickResult(tokens_to_eat=1)

        if not self.has_parsed_expressions:
            if self.expression_state is None:
                self.expression_state = ExpressionState()
                return StateTickResult(child_state=self.expression_state)
            else:
                self._node.conditional_expressions.append(self.expression_state.node)
                self.has_parsed_expressions = True
                self.expression_state = None
                return StateTickResult()

        if not self.has_parsed_else:
            if token.type is TokenType.FI:
                return StateTickResult(is_done=True, tokens_to_eat=1)
            elif token.type is TokenType.ELSE:
                self.has_parsed_else = True
                return StateTickResult(tokens_to_eat=1)
            else:
                self.has_parsed_expressions = False
                return StateTickResult()

        if not self.has_parsed_else_expressions:
            if self.expression_state is None:
                self.expression_state = ExpressionState()
                return StateTickResult(child_state=self.expression_state)
            else:
                self._node.else_expressions.append(self.expression_state.node)
                self.has_parsed_else_expressions = True
                self.expression_state = None

        if token.type is not TokenType.FI:
            self.has_parsed_else_expressions = False
            return StateTickResult()
        return StateTickResult(is_done=True, tokens_to_eat=1)

    @property
    def node(self) -> SyntaxNode:
        return self._node


class Parser(object):
    def __init__(self) -> None:
        self.syntax: List[SyntaxNode] = []
        self.tokens: List[Token] = []
        self.state: Optional[ParserState] = None
        self.state_stack: List[ParserState] = []
        self.nodes: List[SyntaxNode] = []

    def parse(self, tokens: List[Token]) -> List[SyntaxNode]:
        self.tokens.extend(tokens)
        try:
            self._process_tokens()
        except ParseError as e:
            self.reset()
            raise e

        if self.is_done:
            result_nodes = self.nodes
            self.nodes = []
            return result_nodes
        return []

    def _process_tokens(self) -> None:
        if self.state is None:
            self.state = TopLevelExpressionState()
        while self.state is not None:
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
                    new_node = self.state.node
                    if new_node is not None:
                        self.nodes.append(new_node)
                    if len(self.tokens) > 0:
                        self.state = TopLevelExpressionState()
                    else:
                        self.state = None
            if result.is_incomplete:
                break

    def reset(self) -> None:
        self.syntax.clear()
        self.tokens.clear()
        self.state = None
        self.state_stack.clear()
        self.nodes.clear()

    @property
    def is_done(self) -> bool:
        return self.state is None and len(self.state_stack) is 0
