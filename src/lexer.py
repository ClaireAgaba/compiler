"""
MiniLang Compiler — Stage 1: Lexical Analyzer (Lexer)
======================================================
Hand-written character-by-character scanner.
No regex or external libraries — demonstrates true lexer construction.

The lexer reads raw source code and produces a stream of Tokens.

Phases:
  1. Skip whitespace and comments
  2. Recognize keywords and identifiers
  3. Recognize number literals (integer and float)
  4. Recognize string literals (with escape sequences)
  5. Recognize operators and delimiters (including multi-char like ==, !=, <=, >=, ->)
  6. Report errors with line/column info for invalid characters
"""

from typing import List
from .tokens import Token, TokenType, KEYWORDS
from .errors import LexerError


class Lexer:
    """
    Lexical Analyzer for MiniLang.

    Usage:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
    """

    def __init__(self, source: str):
        self.source = source
        self.pos = 0          # Current position in source
        self.line = 1         # Current line number
        self.column = 1       # Current column number
        self.tokens: List[Token] = []
        self.errors: List[LexerError] = []

    def tokenize(self) -> List[Token]:
        """
        Scan the entire source and return a list of tokens.
        Raises LexerError if any invalid characters are found.
        """
        while not self._at_end():
            self._skip_whitespace_and_comments()
            if self._at_end():
                break

            char = self._peek()

            # --- Identifiers and keywords ---
            if char.isalpha() or char == '_':
                self._read_identifier_or_keyword()

            # --- Number literals ---
            elif char.isdigit():
                self._read_number()

            # --- String literals ---
            elif char == '"':
                self._read_string()

            # --- Operators and delimiters ---
            else:
                self._read_operator_or_delimiter()

        # Append EOF token
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))

        if self.errors:
            # Report all errors
            error_messages = "\n".join(e.format() for e in self.errors)
            raise LexerError(f"Lexical errors found:\n{error_messages}")

        return self.tokens

    # ──────────────────────────── Character-level helpers ────────────────────────

    def _at_end(self) -> bool:
        """Check if we've consumed all source characters."""
        return self.pos >= len(self.source)

    def _peek(self) -> str:
        """Look at the current character without consuming it."""
        if self._at_end():
            return '\0'
        return self.source[self.pos]

    def _peek_next(self) -> str:
        """Look at the next character without consuming."""
        if self.pos + 1 >= len(self.source):
            return '\0'
        return self.source[self.pos + 1]

    def _advance(self) -> str:
        """Consume and return the current character, updating line/column."""
        char = self.source[self.pos]
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def _match(self, expected: str) -> bool:
        """Consume the current char if it matches expected."""
        if self._at_end() or self.source[self.pos] != expected:
            return False
        self._advance()
        return True

    def _make_token(self, token_type: TokenType, value, line: int, column: int):
        """Create and append a token."""
        self.tokens.append(Token(token_type, value, line, column))

    # ──────────────────────────── Whitespace & comments ─────────────────────────

    def _skip_whitespace_and_comments(self):
        """Skip whitespace, single-line comments (//), and multi-line comments (/* */)."""
        while not self._at_end():
            char = self._peek()

            # Whitespace
            if char in (' ', '\t', '\r', '\n'):
                self._advance()

            # Single-line comment: //
            elif char == '/' and self._peek_next() == '/':
                self._advance()  # consume first /
                self._advance()  # consume second /
                while not self._at_end() and self._peek() != '\n':
                    self._advance()

            # Multi-line comment: /* ... */
            elif char == '/' and self._peek_next() == '*':
                start_line = self.line
                start_col = self.column
                self._advance()  # consume /
                self._advance()  # consume *
                while not self._at_end():
                    if self._peek() == '*' and self._peek_next() == '/':
                        self._advance()  # consume *
                        self._advance()  # consume /
                        break
                    self._advance()
                else:
                    self.errors.append(
                        LexerError("Unterminated multi-line comment", start_line, start_col)
                    )

            else:
                break  # Not whitespace or comment — done skipping

    # ──────────────────────────── Identifiers & keywords ────────────────────────

    def _read_identifier_or_keyword(self):
        """Read an identifier or keyword token."""
        start_line = self.line
        start_col = self.column
        result = []

        while not self._at_end() and (self._peek().isalnum() or self._peek() == '_'):
            result.append(self._advance())

        word = ''.join(result)

        # Check if it's a keyword
        if word in KEYWORDS:
            token_type = KEYWORDS[word]
            # Handle boolean literals
            if word == 'true':
                self._make_token(TokenType.BOOL_LITERAL, True, start_line, start_col)
            elif word == 'false':
                self._make_token(TokenType.BOOL_LITERAL, False, start_line, start_col)
            else:
                self._make_token(token_type, word, start_line, start_col)
        else:
            self._make_token(TokenType.IDENTIFIER, word, start_line, start_col)

    # ──────────────────────────── Number literals ───────────────────────────────

    def _read_number(self):
        """Read an integer or float literal."""
        start_line = self.line
        start_col = self.column
        result = []
        is_float = False

        while not self._at_end() and self._peek().isdigit():
            result.append(self._advance())

        # Check for decimal point (float)
        if not self._at_end() and self._peek() == '.' and self._peek_next().isdigit():
            is_float = True
            result.append(self._advance())  # consume '.'
            while not self._at_end() and self._peek().isdigit():
                result.append(self._advance())

        number_str = ''.join(result)
        if is_float:
            self._make_token(TokenType.FLOAT_LITERAL, float(number_str), start_line, start_col)
        else:
            self._make_token(TokenType.INTEGER_LITERAL, int(number_str), start_line, start_col)

    # ──────────────────────────── String literals ───────────────────────────────

    def _read_string(self):
        """Read a string literal with escape sequence support."""
        start_line = self.line
        start_col = self.column
        self._advance()  # consume opening "

        result = []
        escape_map = {'n': '\n', 't': '\t', '\\': '\\', '"': '"', '0': '\0'}

        while not self._at_end() and self._peek() != '"':
            if self._peek() == '\n':
                self.errors.append(
                    LexerError("Unterminated string literal", start_line, start_col)
                )
                return
            if self._peek() == '\\':
                self._advance()  # consume backslash
                if self._at_end():
                    self.errors.append(
                        LexerError("Unterminated escape sequence", self.line, self.column)
                    )
                    return
                esc_char = self._advance()
                if esc_char in escape_map:
                    result.append(escape_map[esc_char])
                else:
                    self.errors.append(
                        LexerError(f"Invalid escape sequence: \\{esc_char}", self.line, self.column - 1)
                    )
                    result.append(esc_char)
            else:
                result.append(self._advance())

        if self._at_end():
            self.errors.append(
                LexerError("Unterminated string literal", start_line, start_col)
            )
            return

        self._advance()  # consume closing "
        self._make_token(TokenType.STRING_LITERAL, ''.join(result), start_line, start_col)

    # ──────────────────────────── Operators & delimiters ────────────────────────

    def _read_operator_or_delimiter(self):
        """Read operators (including multi-character) and delimiter tokens."""
        start_line = self.line
        start_col = self.column
        char = self._advance()

        # --- Multi-character operators ---
        if char == '=' and self._match('='):
            self._make_token(TokenType.EQ, '==', start_line, start_col)
        elif char == '!' and self._match('='):
            self._make_token(TokenType.NEQ, '!=', start_line, start_col)
        elif char == '<' and self._match('='):
            self._make_token(TokenType.LTE, '<=', start_line, start_col)
        elif char == '>' and self._match('='):
            self._make_token(TokenType.GTE, '>=', start_line, start_col)
        elif char == '-' and self._match('>'):
            self._make_token(TokenType.ARROW, '->', start_line, start_col)

        # --- Single-character operators ---
        elif char == '+':
            self._make_token(TokenType.PLUS, '+', start_line, start_col)
        elif char == '-':
            self._make_token(TokenType.MINUS, '-', start_line, start_col)
        elif char == '*':
            self._make_token(TokenType.STAR, '*', start_line, start_col)
        elif char == '/':
            self._make_token(TokenType.SLASH, '/', start_line, start_col)
        elif char == '%':
            self._make_token(TokenType.PERCENT, '%', start_line, start_col)
        elif char == '=':
            self._make_token(TokenType.ASSIGN, '=', start_line, start_col)
        elif char == '<':
            self._make_token(TokenType.LT, '<', start_line, start_col)
        elif char == '>':
            self._make_token(TokenType.GT, '>', start_line, start_col)

        # --- Delimiters ---
        elif char == '(':
            self._make_token(TokenType.LPAREN, '(', start_line, start_col)
        elif char == ')':
            self._make_token(TokenType.RPAREN, ')', start_line, start_col)
        elif char == '{':
            self._make_token(TokenType.LBRACE, '{', start_line, start_col)
        elif char == '}':
            self._make_token(TokenType.RBRACE, '}', start_line, start_col)
        elif char == '[':
            self._make_token(TokenType.LBRACKET, '[', start_line, start_col)
        elif char == ']':
            self._make_token(TokenType.RBRACKET, ']', start_line, start_col)
        elif char == ';':
            self._make_token(TokenType.SEMICOLON, ';', start_line, start_col)
        elif char == ':':
            self._make_token(TokenType.COLON, ':', start_line, start_col)
        elif char == ',':
            self._make_token(TokenType.COMMA, ',', start_line, start_col)

        # --- Invalid character ---
        else:
            self.errors.append(
                LexerError(f"Unexpected character: '{char}'", start_line, start_col)
            )
