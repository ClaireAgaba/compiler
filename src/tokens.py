"""
MiniLang Compiler — Token Definitions
=======================================
Defines all token types as an enum and the Token dataclass.
This is the interface between the Lexer and the Parser.

Token categories (as taught in class):
  1. Keywords   — reserved words with fixed meaning (if, while, func, int, ...)
  2. Identifiers — user-defined names for variables and functions
  3. Literals   — constant values written directly in source (42, 3.14, "hi", true)
  4. Operators  — symbols that perform computations or comparisons (+, ==, and, ...)
  5. Delimiters — punctuation that gives code structure ( ; , : ( ) { } [ ] )
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any


class TokenType(Enum):
    """All token types recognized by the MiniLang lexer."""

    # ── 1. KEYWORDS ──────────────────────────────────────────────────────────
    # Reserved words — cannot be used as identifiers.
    # Control-flow keywords
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    RETURN = auto()
    # Declaration keywords
    FUNC = auto()
    VAR = auto()
    # Built-in I/O names are treated as identifiers by the lexer.
    # (Parser handles print(...) and input() semantics contextually.)
    # Boolean value keywords (true/false are keyword literals in MiniLang)
    TRUE = auto()
    FALSE = auto()
    # Logical operator keywords
    AND = auto()
    OR = auto()
    NOT = auto()
    # Type keywords
    INT = auto()
    FLOAT = auto()
    BOOL = auto()
    STRING = auto()
    VOID = auto()

    # ── 2. IDENTIFIERS ───────────────────────────────────────────────────────
    # User-defined names for variables and functions.
    # e.g.  myVar, fibonacci, result_1
    IDENTIFIER = auto()

    # ── 3. LITERALS ──────────────────────────────────────────────────────────
    # Constant values written directly in source code.
    INTEGER_LITERAL = auto()   # e.g.  42
    FLOAT_LITERAL   = auto()   # e.g.  3.14
    STRING_LITERAL  = auto()   # e.g.  "hello"
    BOOL_LITERAL    = auto()   # true  /  false  (value set by lexer)

    # ── 4. OPERATORS ─────────────────────────────────────────────────────────
    # Symbols that perform arithmetic, comparison, assignment, or logic.
    # Arithmetic
    PLUS    = auto()   # +
    MINUS   = auto()   # -
    STAR    = auto()   # *
    SLASH   = auto()   # /
    PERCENT = auto()   # %
    # Comparison
    EQ  = auto()       # ==
    NEQ = auto()       # !=
    LT  = auto()       # <
    GT  = auto()       # >
    LTE = auto()       # <=
    GTE = auto()       # >=
    # Assignment
    ASSIGN = auto()    # =
    # Arrow (return-type annotation)
    ARROW  = auto()    # ->

    # ── 5. DELIMITERS ────────────────────────────────────────────────────────
    # Punctuation that gives code its structure (grouping, termination, separation).
    LPAREN    = auto()  # (   — opens a group / argument list
    RPAREN    = auto()  # )   — closes a group / argument list
    LBRACE    = auto()  # {   — opens a block
    RBRACE    = auto()  # }   — closes a block
    LBRACKET  = auto()  # [   — opens an array index / size
    RBRACKET  = auto()  # ]   — closes an array index / size
    SEMICOLON = auto()  # ;   — statement terminator
    COLON     = auto()  # :   — type annotation separator (var x: int)
    COMMA     = auto()  # ,   — argument / parameter separator

    # ── SPECIAL (internal use) ───────────────────────────────────────────────
    EOF     = auto()    # End of file — signals the parser to stop
    NEWLINE = auto()    # Tracked by lexer for line counting (not emitted)


# Mapping from keyword strings to token types
KEYWORDS = {
    'func': TokenType.FUNC,
    'var': TokenType.VAR,
    'if': TokenType.IF,
    'else': TokenType.ELSE,
    'while': TokenType.WHILE,
    'for': TokenType.FOR,
    'return': TokenType.RETURN,
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
