import enum
from typing import List, Match, Tuple, Pattern, Callable
import re


class TokenType(enum.Enum):
    UNKNOWN = 0
    WHITESPACE = 1
    EOS = 2
    SYMBOL = 3
    REPLACEMENT = 4
    IF = 5
    THEN = 6
    FI = 7
    QUOTES = 8
    ASSIGNMENT = 9


class Token(object):
    @property
    def type(self) -> TokenType:
        return TokenType.UNKNOWN


class SimpleToken(Token):
    def __init__(self, type: TokenType) -> None:
        self._type = type

    def __repr__(self) -> str:
        return '<SimpleToken type: {0}>'.format(self._type)

    @property
    def type(self) -> TokenType:
        return self._type


class SymbolToken(Token):
    def __init__(self) -> None:
        self.value = ''

    def __repr__(self) -> str:
        return '<SymbolToken value: {0}>'.format(self.value)

    @property
    def type(self) -> TokenType:
        return TokenType.SYMBOL


class ReplacementToken(Token):
    def __init__(self) -> None:
        self.value = ''

    def __repr__(self) -> str:
        return '<ReplacementToken value: {0}>'.format(self.value)

    @property
    def type(self) -> TokenType:
        return TokenType.REPLACEMENT


class Lexer(object):
    whitespace_pattern = re.compile(r'^[^\S\n]+')
    newline_pattern = re.compile(r'^\n+')
    semicolon_pattern = re.compile(r'^;')
    quotes_pattern = re.compile(r'^"')
    assignment_pattern = re.compile(r'^=')
    symbol_pattern = re.compile(r'^[a-zA-Z0-9]+')
    simple_replacement_pattern = re.compile(r'^\$([a-zA-Z0-9]+)')
    block_replacement_pattern = re.compile(r'^\${([a-zA-Z0-9]+)}')

    def __init__(self) -> None:
        pass

    def lex_all(self, source: str) -> List[Token]:
        tokens = []
        while len(source) > 0:
            token, source = self.lex(source)
            tokens.append(token)
        return tokens

    def lex(self, source: str) -> Tuple[Token, str]:
        for pattern, lex_func in __class__.PATTERNS:
            match = pattern.match(source)
            if match is None:
                continue
            token = lex_func(self, match)
            substr = source[match.end(0):]
            return token, substr
        return Token(), ''

    def lex_whitespace(self, match: Match) -> Token:
        return SimpleToken(TokenType.WHITESPACE)

    def lex_end_of_statement(self, match: Match) -> Token:
        return SimpleToken(TokenType.EOS)

    def lex_quotes(self, match: Match) -> Token:
        return SimpleToken(TokenType.QUOTES)

    def lex_assignment(self, match: Match) -> Token:
        return SimpleToken(TokenType.ASSIGNMENT)

    def lex_symbol(self, match: Match) -> SymbolToken:
        token = SymbolToken()
        token.value = match.group(0)
        return token

    def lex_replacement(self, match: Match) -> ReplacementToken:
        token = ReplacementToken()
        token.value = match.group(1)
        return token

    PATTERNS: List[Tuple[Pattern, Callable[[Match], Token]]] = [
        (whitespace_pattern, lex_whitespace),
        (newline_pattern, lex_end_of_statement),
        (semicolon_pattern, lex_end_of_statement),
        (quotes_pattern, lex_quotes),
        (assignment_pattern, lex_assignment),
        (symbol_pattern, lex_symbol),
        (simple_replacement_pattern, lex_replacement),
        (block_replacement_pattern, lex_replacement)
    ]
