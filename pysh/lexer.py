import enum
from typing import List, Tuple, Callable, Optional


class TokenType(enum.Enum):
    UNKNOWN = 0
    WHITESPACE = 1
    EOS = 2
    SYMBOL = 3
    DOLLAR_SIGN = 4
    LEFT_CURLY_BRACKET = 5
    RIGHT_CURLY_BRACKET = 6
    IF = 7
    THEN = 8
    ELSE = 9
    FI = 10
    QUOTES = 11
    ASSIGNMENT = 12


class Token(object):
    def __init__(self, type: TokenType, value: str) -> None:
        self.type = type
        self.value = value

    def __repr__(self) -> str:
        return '<Token type: {0}, value: {1}>'.format(self.type, self.value)


class TokenLexDefinition(object):
    def __init__(self, *, pattern: Optional[str] = None, matcher: Optional[Callable[[str], int]] = None,
                 token_func: Optional[Callable[[str], Token]] = None,
                 token_type: Optional[TokenType] = None) -> None:
        self.pattern = pattern
        self.matcher = matcher
        self.token_func = token_func
        self.token_type = token_type

    def match(self, source: str) -> int:
        if self.matcher is not None:
            return self.matcher(source, self.pattern)
        if source.startswith(self.pattern):
            return len(self.pattern)
        return 0


class Lexer(object):
    def __init__(self) -> None:
        self.definitions = self.make_definitions()

    def lex_all(self, source: str) -> List[Token]:
        tokens = []
        while len(source) > 0:
            token, source = self.lex(source)
            tokens.append(token)
        return tokens

    def lex(self, source: str) -> Tuple[Token, str]:
        for definition in self.definitions:
            match_length = definition.match(source)
            if match_length <= 0:
                continue
            value = source[:match_length]
            if definition.token_func is not None:
                token = definition.token_func(value)
            else:
                token = Token(definition.token_type, value)
            return token, source[match_length:]
        return Token(TokenType.UNKNOWN, source[0]), source[1:]

    def match_whitespace(self, source: str, pattern: str) -> int:
        idx = 0
        while idx < len(source):
            val = source[idx]
            if not val.isspace() or val == '\n':
                break
            idx += 1
        return idx

    def match_symbol(self, source: str, pattern: str) -> int:
        idx = 0
        while idx < len(source):
            val = source[idx]
            if not (val.isalnum() or val == '_' or val == '?'):
                break
            idx += 1
        return idx

    def match_keyword(self, source: str, pattern: str) -> int:
        symbol_length = self.match_symbol(source, pattern)
        if source[:symbol_length] == pattern:
            return symbol_length
        return 0

    def make_definitions(self) -> List[TokenLexDefinition]:
        return [
            TokenLexDefinition(matcher=self.match_whitespace, token_type=TokenType.WHITESPACE),
            TokenLexDefinition(pattern='\n', token_type=TokenType.EOS),
            TokenLexDefinition(pattern=';', token_type=TokenType.EOS),
            TokenLexDefinition(pattern='"', token_type=TokenType.QUOTES),
            TokenLexDefinition(pattern='=', token_type=TokenType.ASSIGNMENT),
            TokenLexDefinition(pattern="$", token_type=TokenType.DOLLAR_SIGN),
            TokenLexDefinition(pattern="{", token_type=TokenType.LEFT_CURLY_BRACKET),
            TokenLexDefinition(pattern='}', token_type=TokenType.RIGHT_CURLY_BRACKET),
            TokenLexDefinition(pattern='if', matcher=self.match_keyword, token_type=TokenType.IF),
            TokenLexDefinition(pattern='then', matcher=self.match_keyword, token_type=TokenType.THEN),
            TokenLexDefinition(pattern='else', matcher=self.match_keyword, token_type=TokenType.ELSE),
            TokenLexDefinition(pattern='fi', matcher=self.match_keyword, token_type=TokenType.FI),
            TokenLexDefinition(matcher=self.match_symbol, token_type=TokenType.SYMBOL)
        ]
