# MiniLang Token Specification

This document defines the lexical token set for MiniLang as implemented in the compiler.

## 1. Design Scope

Tokenization (lexical analysis) converts source code characters into a stream of tokens.

Important separation:
- Token definitions are fixed by MiniLang grammar.
- Runtime values entered through `input()` are not tokenized from source; they are runtime VM data.

## 2. Token Categories

MiniLang uses the following token categories:
- Keywords
- Identifiers
- Literals
- Operators
- Delimiters
- Special/Internal

## 3. Keywords (Reserved Words)

Keywords are reserved and cannot be used as identifiers.

| Lexeme | TokenType | Notes |
|---|---|---|
| `func` | `FUNC` | Function declaration start |
| `var` | `VAR` | Variable declaration |
| `if` | `IF` | Conditional |
| `else` | `ELSE` | Conditional alternate branch |
| `while` | `WHILE` | Loop |
| `for` | `FOR` | Loop |
| `return` | `RETURN` | Function return |
| `and` | `AND` | Logical operator keyword |
| `or` | `OR` | Logical operator keyword |
| `not` | `NOT` | Logical unary operator keyword |
| `int` | `INT` | Type keyword |
| `float` | `FLOAT` | Type keyword |
| `bool` | `BOOL` | Type keyword |
| `string` | `STRING` | Type keyword |
| `void` | `VOID` | Type keyword |
| `true` | `TRUE` | Reserved boolean lexeme |
| `false` | `FALSE` | Reserved boolean lexeme |

Lexer behavior note:
- `true` and `false` are recognized as reserved lexemes and emitted as `BOOL_LITERAL` tokens with values `True` and `False`.

## 4. Identifiers

| Pattern | TokenType | Examples |
|---|---|---|
| `[A-Za-z_][A-Za-z0-9_]*` | `IDENTIFIER` | `main`, `x`, `fibonacci`, `result_1`, `print`, `input` |

Rule:
- If a matched identifier lexeme is in the keyword map, emit keyword token instead of `IDENTIFIER`.
- `print` and `input` are intentionally tokenized as `IDENTIFIER` and interpreted contextually by the parser.

## 5. Literals

| Literal Form | TokenType | Value Type |
|---|---|---|
| Integer digits, example `42` | `INTEGER_LITERAL` | `int` |
| Decimal number, example `3.14` | `FLOAT_LITERAL` | `float` |
| Quoted text, example `"hello"` | `STRING_LITERAL` | `str` |
| `true` / `false` | `BOOL_LITERAL` | `bool` |

String literal escapes supported:
- `\n`, `\t`, `\\`, `\"`, `\0`

## 6. Operators

### 6.1 Arithmetic

| Lexeme | TokenType |
|---|---|
| `+` | `PLUS` |
| `-` | `MINUS` |
| `*` | `STAR` |
| `/` | `SLASH` |
| `%` | `PERCENT` |

### 6.2 Comparison

| Lexeme | TokenType |
|---|---|
| `==` | `EQ` |
| `!=` | `NEQ` |
| `<` | `LT` |
| `>` | `GT` |
| `<=` | `LTE` |
| `>=` | `GTE` |

### 6.3 Assignment and Type Arrow

| Lexeme | TokenType |
|---|---|
| `=` | `ASSIGN` |
| `->` | `ARROW` |

### 6.4 Logical Keywords (Operator Role)

| Lexeme | TokenType |
|---|---|
| `and` | `AND` |
| `or` | `OR` |
| `not` | `NOT` |

## 7. Delimiters

| Lexeme | TokenType | Structural Role |
|---|---|---|
| `(` | `LPAREN` | Grouping, call argument list |
| `)` | `RPAREN` | Grouping close |
| `{` | `LBRACE` | Block start |
| `}` | `RBRACE` | Block end |
| `[` | `LBRACKET` | Array index/size start |
| `]` | `RBRACKET` | Array index/size end |
| `;` | `SEMICOLON` | Statement terminator |
| `:` | `COLON` | Type annotation separator |
| `,` | `COMMA` | Item separator |

## 8. Special/Internal Tokens

| TokenType | Purpose |
|---|---|
| `EOF` | End-of-file marker appended by lexer |
| `NEWLINE` | Defined in enum for internal/possible future use (not emitted in current lexer flow) |

## 9. Lexical Ignored Elements

The lexer skips these and does not emit tokens:
- Whitespace: spaces, tabs, carriage returns, newlines
- Single-line comments: `// ...`
- Multi-line comments: `/* ... */`

## 10. Error Conditions (Lexer)

Lexer raises lexical errors for:
- Invalid/unknown characters
- Unterminated string literal
- Invalid escape sequence
- Unterminated multi-line comment

## 11. Practical Demo Note (Dynamic Input)

Dynamic runtime input should be provided as values, not expressions.

Correct:
- Code: `var x: int = input(); print(x * 5 - 2);`
- Runtime input: `7`

Incorrect:
- Runtime input: `x*5-2` or `7-2`

Reason:
- Expressions are parsed from source code tokens.
- Runtime input is consumed by VM as raw values.