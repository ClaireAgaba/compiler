"""
MiniLang Compiler — Stage 2: Parser (Recursive Descent)
=========================================================
Implements a top-down recursive descent parser (LL(1)) that reads
a token stream and produces an Abstract Syntax Tree (AST).

The parser implements operator precedence through the grammar structure:
  lowest  →  or  →  and  →  ==,!=  →  <,>,<=,>=  →  +,-  →  *,/,%  →  unary  →  call  →  primary  →  highest

This is a PREDICTIVE parser — it looks at the current token to decide
which production rule to apply (top-down parsing approach).

Error recovery: synchronizes at statement boundaries to report multiple errors.
"""

from typing import List, Optional
from .tokens import Token, TokenType
from .ast_nodes import *
from .errors import ParseError


class Parser:
    """
    Recursive Descent Parser for MiniLang.

    Usage:
        parser = Parser(tokens)
        ast = parser.parse()
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.errors: List[ParseError] = []

    # ──────────────────────────── Token-level helpers ───────────────────────────

    def _current(self) -> Token:
        """Return the current token."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF

    def _peek(self) -> TokenType:
        """Return the type of the current token."""
        return self._current().type

    def _peek_token(self, offset: int = 0) -> Token:
        """Return token at current position + offset (clamped to EOF)."""
        index = min(self.pos + offset, len(self.tokens) - 1)
        return self.tokens[index]

    def _advance(self) -> Token:
        """Consume and return the current token."""
        token = self._current()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token

    def _check(self, *types: TokenType) -> bool:
        """Check if current token is one of the given types."""
        return self._peek() in types

    def _match(self, *types: TokenType) -> Optional[Token]:
        """Consume current token if it matches one of the given types."""
        if self._peek() in types:
            return self._advance()
        return None

    def _expect(self, token_type: TokenType, message: str = "") -> Token:
        """Consume current token if it matches, otherwise raise ParseError."""
        if self._peek() == token_type:
            return self._advance()
        token = self._current()
        if not message:
            message = f"Expected {token_type.name}, got {token.type.name} ('{token.value}')"
        raise ParseError(message, token.line, token.column)

    # ──────────────────────────── Error recovery ───────────────────────────────

    def _synchronize(self):
        """
        Skip tokens until we reach a statement boundary.
        This allows us to recover from errors and continue parsing.
        """
        self._advance()
        while not self._check(TokenType.EOF):
            # After a semicolon, we can start a new statement
            if self.tokens[self.pos - 1].type == TokenType.SEMICOLON:
                return
            # These tokens often begin statements
            if self._peek() in (
                TokenType.FUNC, TokenType.VAR, TokenType.IF,
                TokenType.WHILE, TokenType.FOR, TokenType.RETURN,
                TokenType.RBRACE
            ):
                return
            if self._peek() == TokenType.IDENTIFIER and self._current().value == 'print':
                return
            self._advance()

    # ──────────────────────────── MAIN ENTRY POINT ─────────────────────────────

    def parse(self) -> ProgramNode:
        """
        Parse the token stream into an AST.

        Grammar: program → function* EOF
        """
        program = ProgramNode(line=1, column=1)

        while not self._check(TokenType.EOF):
            try:
                func = self._parse_function()
                program.functions.append(func)
            except ParseError as e:
                self.errors.append(e)
                self._synchronize()

        if self.errors:
            error_messages = "\n".join(e.format() for e in self.errors)
            raise ParseError(f"Parse errors found:\n{error_messages}")

        return program

    # ──────────────────────────── DECLARATIONS ─────────────────────────────────

    def _parse_function(self) -> FunctionNode:
        """
        Parse a function declaration.
        Grammar: function → "func" IDENT "(" params? ")" "->" type block
        """
        func_token = self._expect(TokenType.FUNC, "Expected 'func' keyword")
        name_token = self._expect(TokenType.IDENTIFIER, "Expected function name")

        self._expect(TokenType.LPAREN, "Expected '(' after function name")
        params = self._parse_params()
        self._expect(TokenType.RPAREN, "Expected ')' after parameters")

        self._expect(TokenType.ARROW, "Expected '->' before return type")
        return_type = self._parse_type()

        body = self._parse_block()

        return FunctionNode(
            name=name_token.value,
            params=params,
            return_type=return_type,
            body=body,
            line=func_token.line,
            column=func_token.column,
        )

    def _parse_params(self) -> List[ParamNode]:
        """
        Parse function parameters.
        Grammar: params → param ("," param)*
                 param  → IDENT ":" type
        """
        params = []
        if not self._check(TokenType.RPAREN):
            params.append(self._parse_param())
            while self._match(TokenType.COMMA):
                params.append(self._parse_param())
        return params

    def _parse_param(self) -> ParamNode:
        """Parse a single parameter: IDENT ":" type"""
        name_token = self._expect(TokenType.IDENTIFIER, "Expected parameter name")
        self._expect(TokenType.COLON, "Expected ':' after parameter name")
        param_type = self._parse_type()
        return ParamNode(
            name=name_token.value,
            param_type=param_type,
            line=name_token.line,
            column=name_token.column,
        )

    def _parse_type(self) -> str:
        """
        Parse a type specifier.
        Grammar: type → "int" | "float" | "bool" | "string" | "void" | type "[" INT "]"
        """
        type_token = self._match(
            TokenType.INT, TokenType.FLOAT, TokenType.BOOL,
            TokenType.STRING, TokenType.VOID
        )
        if not type_token:
            raise ParseError(
                f"Expected type, got {self._current().type.name}",
                self._current().line, self._current().column
            )

        type_name = type_token.value

        # Check for array type: type[size]
        if self._match(TokenType.LBRACKET):
            size_token = self._expect(TokenType.INTEGER_LITERAL, "Expected array size")
            self._expect(TokenType.RBRACKET, "Expected ']' after array size")
            return f"{type_name}[{size_token.value}]"

        return type_name

    def _parse_var_decl(self) -> VarDeclNode:
        """
        Parse a variable declaration.
        Grammar: var_decl → "var" IDENT ":" type ("=" expr)? ";"
        """
        var_token = self._expect(TokenType.VAR)
        name_token = self._expect(TokenType.IDENTIFIER, "Expected variable name")
        self._expect(TokenType.COLON, "Expected ':' after variable name")

        var_type = self._parse_type()

        # Check for array type
        array_size = None
        if '[' in var_type:
            # Extract base type and size: "int[10]" → "int", 10
            base = var_type.split('[')[0]
            size_str = var_type.split('[')[1].rstrip(']')
            array_size = int(size_str)
            var_type = base

        initializer = None
        if self._match(TokenType.ASSIGN):
            initializer = self._parse_expression()

        self._expect(TokenType.SEMICOLON, "Expected ';' after variable declaration")

        return VarDeclNode(
            name=name_token.value,
            var_type=var_type,
            initializer=initializer,
            array_size=array_size,
            line=var_token.line,
            column=var_token.column,
        )

    # ──────────────────────────── STATEMENTS ───────────────────────────────────

    def _parse_block(self) -> BlockNode:
        """
        Parse a block of statements.
        Grammar: block → "{" statement* "}"
        """
        brace = self._expect(TokenType.LBRACE, "Expected '{'")
        statements = []

        while not self._check(TokenType.RBRACE, TokenType.EOF):
            try:
                stmt = self._parse_statement()
                statements.append(stmt)
            except ParseError as e:
                self.errors.append(e)
                self._synchronize()

        self._expect(TokenType.RBRACE, "Expected '}'")

        return BlockNode(
            statements=statements,
            line=brace.line,
            column=brace.column,
        )

    def _parse_statement(self) -> ASTNode:
        """
        Parse a single statement.
        Grammar: statement → var_decl | if_stmt | while_stmt | for_stmt
                           | return_stmt | print_stmt | assignment | expr_stmt
        """
        if self._check(TokenType.VAR):
            return self._parse_var_decl()
        elif self._check(TokenType.IF):
            return self._parse_if()
        elif self._check(TokenType.WHILE):
            return self._parse_while()
        elif self._check(TokenType.FOR):
            return self._parse_for()
        elif self._check(TokenType.RETURN):
            return self._parse_return()
        elif self._check(TokenType.IDENTIFIER) and self._current().value == 'print':
            return self._parse_print()
        else:
            return self._parse_assignment_or_expr()

    def _parse_if(self) -> IfNode:
        """
        Parse an if statement.
        Grammar: if_stmt → "if" "(" expr ")" block ("else" ("if" ... | block))?
        """
        if_token = self._advance()  # consume 'if'
        self._expect(TokenType.LPAREN, "Expected '(' after 'if'")
        condition = self._parse_expression()
        self._expect(TokenType.RPAREN, "Expected ')' after condition")
        then_block = self._parse_block()

        else_block = None
        if self._match(TokenType.ELSE):
            if self._check(TokenType.IF):
                # else if → wrap the nested if in a block
                nested_if = self._parse_if()
                else_block = BlockNode(
                    statements=[nested_if],
                    line=nested_if.line,
                    column=nested_if.column,
                )
            else:
                else_block = self._parse_block()

        return IfNode(
            condition=condition,
            then_block=then_block,
            else_block=else_block,
            line=if_token.line,
            column=if_token.column,
        )

    def _parse_while(self) -> WhileNode:
        """
        Parse a while loop.
        Grammar: while_stmt → "while" "(" expr ")" block
        """
        while_token = self._advance()  # consume 'while'
        self._expect(TokenType.LPAREN, "Expected '(' after 'while'")
        condition = self._parse_expression()
        self._expect(TokenType.RPAREN, "Expected ')' after condition")
        body = self._parse_block()

        return WhileNode(
            condition=condition,
            body=body,
            line=while_token.line,
            column=while_token.column,
        )

    def _parse_for(self) -> ForNode:
        """
        Parse a for loop.
        Grammar: for_stmt → "for" "(" (var_decl | ";") expr? ";" assignment? ")" block
        """
        for_token = self._advance()  # consume 'for'
        self._expect(TokenType.LPAREN, "Expected '(' after 'for'")

        # Init
        init = None
        if self._check(TokenType.VAR):
            init = self._parse_var_decl()  # This already consumes the semicolon
        else:
            self._expect(TokenType.SEMICOLON, "Expected ';' in for loop")

        # Condition
        condition = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._parse_expression()
        self._expect(TokenType.SEMICOLON, "Expected ';' after for condition")

        # Update
        update = None
        if not self._check(TokenType.RPAREN):
            # Parse as assignment expression (without semicolon)
            expr = self._parse_expression()
            if self._check(TokenType.ASSIGN):
                # It's an assignment
                self._advance()
                value = self._parse_expression()
                update = AssignNode(
                    target=expr, value=value,
                    line=expr.line, column=expr.column
                )
            else:
                update = ExprStmtNode(expression=expr, line=expr.line, column=expr.column)

        self._expect(TokenType.RPAREN, "Expected ')' after for clauses")
        body = self._parse_block()

        return ForNode(
            init=init,
            condition=condition,
            update=update,
            body=body,
            line=for_token.line,
            column=for_token.column,
        )

    def _parse_return(self) -> ReturnNode:
        """
        Parse a return statement.
        Grammar: return_stmt → "return" expr? ";"
        """
        ret_token = self._advance()  # consume 'return'
        value = None
        if not self._check(TokenType.SEMICOLON):
            value = self._parse_expression()
        self._expect(TokenType.SEMICOLON, "Expected ';' after return")

        return ReturnNode(
            value=value,
            line=ret_token.line,
            column=ret_token.column,
        )

    def _parse_print(self) -> PrintNode:
        """
        Parse a print statement.
        Grammar: print_stmt → "print" "(" expr ")" ";"
        """
        print_token = self._expect(TokenType.IDENTIFIER, "Expected 'print'")
        if print_token.value != 'print':
            raise ParseError("Expected 'print'", print_token.line, print_token.column)
        self._expect(TokenType.LPAREN, "Expected '(' after 'print'")
        value = self._parse_expression()
        self._expect(TokenType.RPAREN, "Expected ')' after print argument")
        self._expect(TokenType.SEMICOLON, "Expected ';' after print statement")

        return PrintNode(
            value=value,
            line=print_token.line,
            column=print_token.column,
        )

    def _parse_assignment_or_expr(self) -> ASTNode:
        """
        Parse an assignment or expression statement.
        We parse the left side as an expression, then check for '=' to decide.
        """
        expr = self._parse_expression()

        if self._match(TokenType.ASSIGN):
            value = self._parse_expression()
            self._expect(TokenType.SEMICOLON, "Expected ';' after assignment")
            return AssignNode(
                target=expr, value=value,
                line=expr.line, column=expr.column
            )

        self._expect(TokenType.SEMICOLON, "Expected ';' after expression")
        return ExprStmtNode(
            expression=expr,
            line=expr.line, column=expr.column
        )

    # ──────────────────────────── EXPRESSIONS (by precedence) ──────────────────

    def _parse_expression(self) -> ASTNode:
        """Entry point for expression parsing — starts at lowest precedence."""
        return self._parse_or()

    def _parse_or(self) -> ASTNode:
        """Grammar: logic_or → logic_and ("or" logic_and)*"""
        left = self._parse_and()
        while self._match(TokenType.OR):
            right = self._parse_and()
            left = BinaryOpNode(
                op="or", left=left, right=right,
                line=left.line, column=left.column
            )
        return left

    def _parse_and(self) -> ASTNode:
        """Grammar: logic_and → equality ("and" equality)*"""
        left = self._parse_equality()
        while self._match(TokenType.AND):
            right = self._parse_equality()
            left = BinaryOpNode(
                op="and", left=left, right=right,
                line=left.line, column=left.column
            )
        return left

    def _parse_equality(self) -> ASTNode:
        """Grammar: equality → comparison (("==" | "!=") comparison)*"""
        left = self._parse_comparison()
        while True:
            op_token = self._match(TokenType.EQ, TokenType.NEQ)
            if not op_token:
                break
            right = self._parse_comparison()
            left = BinaryOpNode(
                op=op_token.value, left=left, right=right,
                line=left.line, column=left.column
            )
        return left

    def _parse_comparison(self) -> ASTNode:
        """Grammar: comparison → addition (("<" | ">" | "<=" | ">=") addition)*"""
        left = self._parse_addition()
        while True:
            op_token = self._match(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE)
            if not op_token:
                break
            right = self._parse_addition()
            left = BinaryOpNode(
                op=op_token.value, left=left, right=right,
                line=left.line, column=left.column
            )
        return left

    def _parse_addition(self) -> ASTNode:
        """Grammar: addition → multiplication (("+" | "-") multiplication)*"""
        left = self._parse_multiplication()
        while True:
            op_token = self._match(TokenType.PLUS, TokenType.MINUS)
            if not op_token:
                break
            right = self._parse_multiplication()
            left = BinaryOpNode(
                op=op_token.value, left=left, right=right,
                line=left.line, column=left.column
            )
        return left

    def _parse_multiplication(self) -> ASTNode:
        """Grammar: multiplication → unary (("*" | "/" | "%") unary)*"""
        left = self._parse_unary()
        while True:
            op_token = self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT)
            if not op_token:
                break
            right = self._parse_unary()
            left = BinaryOpNode(
                op=op_token.value, left=left, right=right,
                line=left.line, column=left.column
            )
        return left

    def _parse_unary(self) -> ASTNode:
        """Grammar: unary → ("not" | "-") unary | call"""
        if self._check(TokenType.NOT):
            op = self._advance()
            operand = self._parse_unary()
            return UnaryOpNode(
                op="not", operand=operand,
                line=op.line, column=op.column
            )
        if self._check(TokenType.MINUS):
            op = self._advance()
            operand = self._parse_unary()
            return UnaryOpNode(
                op="-", operand=operand,
                line=op.line, column=op.column
            )
        return self._parse_call()

    def _parse_call(self) -> ASTNode:
        """
        Grammar: call → primary ("(" args? ")" | "[" expr "]")*
        Handles function calls and array access.
        """
        expr = self._parse_primary()

        while True:
            if self._match(TokenType.LPAREN):
                # Function call
                args = []
                if not self._check(TokenType.RPAREN):
                    args.append(self._parse_expression())
                    while self._match(TokenType.COMMA):
                        args.append(self._parse_expression())
                self._expect(TokenType.RPAREN, "Expected ')' after arguments")

                if isinstance(expr, IdentifierNode):
                    expr = FunctionCallNode(
                        name=expr.name, arguments=args,
                        line=expr.line, column=expr.column
                    )
                else:
                    raise ParseError(
                        "Can only call functions by name",
                        expr.line, expr.column
                    )
            elif self._match(TokenType.LBRACKET):
                # Array access
                index = self._parse_expression()
                self._expect(TokenType.RBRACKET, "Expected ']' after index")
                expr = ArrayAccessNode(
                    array=expr, index=index,
                    line=expr.line, column=expr.column
                )
            else:
                break

        return expr

    def _parse_primary(self) -> ASTNode:
        """
        Grammar: primary → NUMBER | STRING | "true" | "false" | IDENT
                         | "(" expr ")" | "input" "(" ")"
        """
        token = self._current()

        # Integer literal
        if self._match(TokenType.INTEGER_LITERAL):
            return NumberNode(value=token.value, line=token.line, column=token.column)

        # Float literal
        if self._match(TokenType.FLOAT_LITERAL):
            return NumberNode(value=token.value, line=token.line, column=token.column)

        # String literal
        if self._match(TokenType.STRING_LITERAL):
            return StringNode(value=token.value, line=token.line, column=token.column)

        # Boolean literal
        if self._match(TokenType.BOOL_LITERAL):
            return BoolNode(value=token.value, line=token.line, column=token.column)

        # Input expression parsed contextually as identifier call: input()
        if (
            self._check(TokenType.IDENTIFIER)
            and token.value == 'input'
            and self._peek_token(1).type == TokenType.LPAREN
            and self._peek_token(2).type == TokenType.RPAREN
        ):
            self._advance()  # consume 'input'
            self._advance()  # consume '('
            self._advance()  # consume ')'
            return InputNode(line=token.line, column=token.column)

        # Identifier
        if self._match(TokenType.IDENTIFIER):
            return IdentifierNode(name=token.value, line=token.line, column=token.column)

        # Grouped expression
        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        raise ParseError(
            f"Unexpected token: {token.type.name} ('{token.value}')",
            token.line, token.column
        )
