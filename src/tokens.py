"""
MiniLang Compiler — Token Definitions
=======================================
Defines all token types as an enum and the Token dataclass.
This is the interface between the Lexer and the Parser.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any


class TokenType(Enum):
    """All token types recognized by the MiniLang lexer."""

    # --- Literals ---
    INTEGER_LITERAL = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()
    BOOL_LITERAL = auto()

    # --- Identifier ---
    IDENTIFIER = auto()

    # --- Keywords ---
    FUNC = auto()
    VAR = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    RETURN = auto()
    PRINT = auto()
    INPUT = auto()
    TRUE = auto()
    FALSE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

    # --- Type keywords ---
    INT = auto()
    FLOAT = auto()
    BOOL = auto()
    STRING = auto()
    VOID = auto()

    # --- Arithmetic operators ---
    PLUS = auto()        # +
    MINUS = auto()       # -
    STAR = auto()        # *
    SLASH = auto()       # /
    PERCENT = auto()     # %

    # --- Comparison operators ---
    EQ = auto()          # ==
    NEQ = auto()         # !=
    LT = auto()          # <
    GT = auto()          # >
    LTE = auto()         # <=
    GTE = auto()         # >=

    # --- Assignment ---
    ASSIGN = auto()      # =

    # --- Arrow ---
    ARROW = auto()       # ->

    # --- Delimiters ---
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    LBRACE = auto()      # {
    RBRACE = auto()      # }
    LBRACKET = auto()    # [
    RBRACKET = auto()    # ]
    SEMICOLON = auto()   # ;
    COLON = auto()       # :
    COMMA = auto()       # ,

    # --- Special ---
    EOF = auto()
    NEWLINE = auto()


# Mapping from keyword strings to token types
KEYWORDS = {
    'func': TokenType.FUNC,
    'var': TokenType.VAR,
    'if': TokenType.IF,
    'else': TokenType.ELSE,
    'while': TokenType.WHILE,
    'for': TokenType.FOR,
    'return': TokenType.RETURN,
    'print': TokenType.PRINT,
    'input': TokenType.INPUT,
    'true': TokenType.TRUE,
    'false': TokenType.FALSE,
    'and': TokenType.AND,
    'or': TokenType.OR,
    'not': TokenType.NOT,
    'int': TokenType.INT,
    'float': TokenType.FLOAT,
    'bool': TokenType.BOOL,
    'string': TokenType.STRING,
    'void': TokenType.VOID,
}


@dataclass
class Token:
    """
    A single token produced by the lexer.

    Attributes:
        type:   The TokenType enum value.
        value:  The literal value (string text, number, etc.).
        line:   Source line number (1-indexed).
        column: Source column number (1-indexed).
    """
    type: TokenType
    value: Any
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.column})"
