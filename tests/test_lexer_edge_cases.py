import unittest

from src.errors import LexerError
from src.lexer import Lexer
from src.tokens import TokenType


def tokenize(source: str):
    return Lexer(source).tokenize()


class LexerEdgeCaseTests(unittest.TestCase):
    def test_keywords_vs_identifiers(self):
        source = "func main() -> void { var ifx: int = 1; print(ifx); }"
        tokens = tokenize(source)
        pairs = [(tok.type, tok.value) for tok in tokens]

        self.assertIn((TokenType.FUNC, "func"), pairs)
        self.assertIn((TokenType.VAR, "var"), pairs)
        self.assertIn((TokenType.IDENTIFIER, "print"), pairs)
        self.assertIn((TokenType.IDENTIFIER, "main"), pairs)
        self.assertIn((TokenType.IDENTIFIER, "ifx"), pairs)

    def test_boolean_lexemes_emit_bool_literals(self):
        tokens = tokenize("var a: bool = true; var b: bool = false;")
        bool_values = [tok.value for tok in tokens if tok.type == TokenType.BOOL_LITERAL]
        self.assertEqual(bool_values, [True, False])

    def test_all_delimiters(self):
        tokens = tokenize("(){ }[];:,")
        token_types = [tok.type for tok in tokens]
        self.assertEqual(
            token_types,
            [
                TokenType.LPAREN,
                TokenType.RPAREN,
                TokenType.LBRACE,
                TokenType.RBRACE,
                TokenType.LBRACKET,
                TokenType.RBRACKET,
                TokenType.SEMICOLON,
                TokenType.COLON,
                TokenType.COMMA,
                TokenType.EOF,
            ],
        )

    def test_multi_char_and_single_char_operators(self):
        tokens = tokenize("a<=b a>=b a==b a!=b a->b a<b a>b a=b a-b")
        types = [tok.type for tok in tokens]
        expected = [
            TokenType.IDENTIFIER,
            TokenType.LTE,
            TokenType.IDENTIFIER,
            TokenType.IDENTIFIER,
            TokenType.GTE,
            TokenType.IDENTIFIER,
            TokenType.IDENTIFIER,
            TokenType.EQ,
            TokenType.IDENTIFIER,
            TokenType.IDENTIFIER,
            TokenType.NEQ,
            TokenType.IDENTIFIER,
            TokenType.IDENTIFIER,
            TokenType.ARROW,
            TokenType.IDENTIFIER,
            TokenType.IDENTIFIER,
            TokenType.LT,
            TokenType.IDENTIFIER,
            TokenType.IDENTIFIER,
            TokenType.GT,
            TokenType.IDENTIFIER,
            TokenType.IDENTIFIER,
            TokenType.ASSIGN,
            TokenType.IDENTIFIER,
            TokenType.IDENTIFIER,
            TokenType.MINUS,
            TokenType.IDENTIFIER,
            TokenType.EOF,
        ]
        self.assertEqual(types, expected)

    def test_numbers_and_strings(self):
        tokens = tokenize("42 3.14 \"A\\nB\"")
        values = [tok.value for tok in tokens if tok.type != TokenType.EOF]
        self.assertEqual(values, [42, 3.14, "A\nB"])

    def test_comments_are_ignored(self):
        source = "var x: int = 1; // ignore\n/* and ignore */ var y: int = 2;"
        tokens = tokenize(source)
        identifiers = [tok.value for tok in tokens if tok.type == TokenType.IDENTIFIER]
        self.assertEqual(identifiers, ["x", "y"])

    def test_unterminated_multiline_comment_error(self):
        with self.assertRaises(LexerError) as ctx:
            tokenize("/* missing close")
        self.assertIn("Unterminated multi-line comment", str(ctx.exception))

    def test_unterminated_string_error(self):
        with self.assertRaises(LexerError) as ctx:
            tokenize('"hello')
        self.assertIn("Unterminated string literal", str(ctx.exception))

    def test_invalid_escape_sequence_error(self):
        with self.assertRaises(LexerError) as ctx:
            tokenize('"bad\\q"')
        self.assertIn("Invalid escape sequence", str(ctx.exception))

    def test_invalid_character_error(self):
        with self.assertRaises(LexerError) as ctx:
            tokenize("var x: int = 1 @")
        self.assertIn("Unexpected character", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()