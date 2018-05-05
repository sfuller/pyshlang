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
    IF = 5
    THEN = 6
    FI = 7
    QUOTES = 8
    ASSIGNMENT = 9


class Token(object):
    def __init__(self, type: TokenType, value: str) -> None:
        self.type = type
        self.value = value

    def __repr__(self) -> str:
        return '<Token type: {0}, value: {1}>'.format(self.type, self.value)


class TokenLexDefinition(object):
    def __init__(self, *, character: Optional[str] = None, matcher: Optional[Callable[[str], bool]] = None,
                 is_compound=False, token_func: Optional[Callable[[str], Token]] = None,
                 token_type: Optional[TokenType] = None) -> None:
        self.character = character
        self.matcher = matcher
        self.is_compound = is_compound
        self.token_func = token_func
        self.token_type = token_type

    def is_match(self, char: str) -> bool:
        if self.matcher is not None:
            return self.matcher(char)
        return self.character == char


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
        character = source[0]
        for definition in self.definitions:
            is_match = definition.is_match(character)
            if not is_match:
                continue
            end_index = 1
            if definition.is_compound:
                while end_index < len(source):
                    # Subsequent characters must not match other definitions
                    next_character = source[end_index]
                    is_same_def = False
                    for other_def in self.definitions:
                        if other_def is definition:
                            is_same_def = True
                            break
                        if other_def.is_match(next_character):
                            break
                    if not is_same_def or not definition.is_match(next_character):
                        break
                    end_index += 1
            value = source[:end_index]
            if definition.token_func is not None:
                token = definition.token_func(value)
            else:
                token = Token(definition.token_type, value)
            return token, source[end_index:]
        return Token(TokenType.UNKNOWN, character), source[1:]

    def is_whitespace(self, value: str) -> bool:
        return value.isspace() and value != '\n'

    def is_symbol(self, value: str) -> bool:
        return True

    def make_definitions(self) -> List[TokenLexDefinition]:
        return [
            TokenLexDefinition(matcher=self.is_whitespace, is_compound=True, token_type=TokenType.WHITESPACE),
            TokenLexDefinition(character='\n', is_compound=True, token_type=TokenType.EOS),
            TokenLexDefinition(character=';', token_type=TokenType.EOS),
            TokenLexDefinition(character='"', token_type=TokenType.QUOTES),
            TokenLexDefinition(character='=', token_type=TokenType.ASSIGNMENT),
            TokenLexDefinition(character="$", token_type=TokenType.DOLLAR_SIGN),
            TokenLexDefinition(character="{", token_type=TokenType.LEFT_CURLY_BRACKET),
            TokenLexDefinition(character='}', token_type=TokenType.RIGHT_CURLY_BRACKET),
            TokenLexDefinition(matcher=self.is_symbol, is_compound=True, token_type=TokenType.SYMBOL)
        ]
