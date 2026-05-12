"""
MiniLang Compiler — Stage 3: Semantic Analyzer
================================================
Tree-walking semantic analyzer that validates the AST and annotates
it with type information.

Performs:
  1. Name resolution — all variables/functions must be declared before use
  2. Type checking — type compatibility in assignments, operations, calls
  3. Type inference — resolves expression types bottom-up
  4. Function validation — argument count/types, return type matching
  5. Control flow checks — return statements in non-void functions
  6. Duplicate detection — no re-declaring in the same scope
  7. Main function check — ensure main() exists
"""

from typing import Optional, List
from .ast_nodes import *
from .symbol_table import SymbolTable, Symbol
from .errors import SemanticError


class SemanticAnalyzer:
    """
    Semantic Analyzer for MiniLang.

    Usage:
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)  # Raises SemanticError on failure
        # AST nodes are now annotated with resolved_type
    """

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors: List[SemanticError] = []
        self.current_function: Optional[FunctionNode] = None  # Track current function for return checks

    def analyze(self, program: ProgramNode):
        """
        Perform semantic analysis on the entire program AST.
        Annotates AST nodes with resolved types.
        Raises SemanticError if any semantic errors are found.
        """
        # First pass: register all functions (allows forward references)
        for func in program.functions:
            param_types = [p.param_type for p in func.params]
            try:
                self.symbol_table.define(
                    func.name, 'function', 'function',
                    params=param_types, return_type=func.return_type
                )
            except ValueError:
                self._error(f"Function '{func.name}' already defined", func.line, func.column)

        # Second pass: analyze function bodies
        for func in program.functions:
            self._analyze_function(func)

        # Check that main() exists
        main_sym = self.symbol_table.lookup('main')
        if not main_sym or main_sym.kind != 'function':
            self._error("No 'main' function defined", 1, 1)

        if self.errors:
            error_messages = "\n".join(e.format() for e in self.errors)
            raise SemanticError(f"Semantic errors found:\n{error_messages}")

    def _error(self, message: str, line: int, column: int):
        """Record a semantic error."""
        self.errors.append(SemanticError(message, line, column))

    # ──────────────────────────── FUNCTION ANALYSIS ────────────────────────────

    def _analyze_function(self, func: FunctionNode):
        """Analyze a function declaration and its body."""
        old_function = self.current_function
        self.current_function = func

        self.symbol_table.enter_scope()

        # Define parameters in the function scope
        for param in func.params:
            try:
                self.symbol_table.define(param.name, param.param_type, 'parameter')
            except ValueError:
                self._error(
                    f"Duplicate parameter name: '{param.name}'",
                    param.line, param.column
                )

        # Analyze function body
        self._analyze_block(func.body)

        # Check return for non-void functions
        if func.return_type != 'void':
            if not self._has_return(func.body):
                self._error(
                    f"Function '{func.name}' must return a value of type '{func.return_type}'",
                    func.line, func.column
                )

        self.symbol_table.exit_scope()
        self.current_function = old_function

    def _has_return(self, block: BlockNode) -> bool:
        """Check if a block always returns a value."""
        for stmt in block.statements:
            if isinstance(stmt, ReturnNode):
                return True
            if isinstance(stmt, IfNode):
                then_returns = self._has_return(stmt.then_block)
                else_returns = stmt.else_block and self._has_return(stmt.else_block)
                if then_returns and else_returns:
                    return True
        return False

    # ──────────────────────────── STATEMENT ANALYSIS ───────────────────────────

    def _analyze_block(self, block: BlockNode):
        """Analyze a block of statements."""
        for stmt in block.statements:
            self._analyze_statement(stmt)

    def _analyze_statement(self, stmt: ASTNode):
        """Dispatch to the appropriate statement analyzer."""
        if isinstance(stmt, VarDeclNode):
            self._analyze_var_decl(stmt)
        elif isinstance(stmt, AssignNode):
            self._analyze_assign(stmt)
        elif isinstance(stmt, IfNode):
            self._analyze_if(stmt)
        elif isinstance(stmt, WhileNode):
            self._analyze_while(stmt)
        elif isinstance(stmt, ForNode):
            self._analyze_for(stmt)
        elif isinstance(stmt, ReturnNode):
            self._analyze_return(stmt)
        elif isinstance(stmt, PrintNode):
            self._analyze_print(stmt)
        elif isinstance(stmt, ExprStmtNode):
            self._analyze_expression(stmt.expression)

    def _analyze_var_decl(self, node: VarDeclNode):
        """Analyze a variable declaration."""
        # Check initializer type if present
        if node.initializer:
            init_type = self._analyze_expression(node.initializer)
            if init_type and init_type != node.var_type:
                # Allow int -> float promotion
                if not (node.var_type == 'float' and init_type == 'int'):
                    self._error(
                        f"Cannot assign {init_type} to variable '{node.name}' of type {node.var_type}",
                        node.line, node.column
                    )

        # Define the variable in current scope
        try:
            self.symbol_table.define(
                node.name, node.var_type, 'variable',
                array_size=node.array_size
            )
        except ValueError:
            self._error(
                f"Variable '{node.name}' already defined in this scope",
                node.line, node.column
            )

    def _analyze_assign(self, node: AssignNode):
        """Analyze an assignment statement."""
        target_type = self._analyze_expression(node.target)
        value_type = self._analyze_expression(node.value)

        if target_type and value_type:
            if target_type != value_type:
                if not (target_type == 'float' and value_type == 'int'):
                    self._error(
                        f"Cannot assign {value_type} to {target_type}",
                        node.line, node.column
                    )

        # Ensure target is assignable (identifier or array access)
        if not isinstance(node.target, (IdentifierNode, ArrayAccessNode)):
            self._error("Invalid assignment target", node.line, node.column)

    def _analyze_if(self, node: IfNode):
        """Analyze an if statement."""
        cond_type = self._analyze_expression(node.condition)
        if cond_type and cond_type != 'bool':
            self._error(
                f"If condition must be bool, got {cond_type}",
                node.condition.line, node.condition.column
            )

        self.symbol_table.enter_scope()
        self._analyze_block(node.then_block)
        self.symbol_table.exit_scope()

        if node.else_block:
            self.symbol_table.enter_scope()
            self._analyze_block(node.else_block)
            self.symbol_table.exit_scope()

    def _analyze_while(self, node: WhileNode):
        """Analyze a while loop."""
        cond_type = self._analyze_expression(node.condition)
        if cond_type and cond_type != 'bool':
            self._error(
                f"While condition must be bool, got {cond_type}",
                node.condition.line, node.condition.column
            )

        self.symbol_table.enter_scope()
        self._analyze_block(node.body)
        self.symbol_table.exit_scope()

    def _analyze_for(self, node: ForNode):
        """Analyze a for loop."""
        self.symbol_table.enter_scope()

        if node.init:
            self._analyze_statement(node.init)
        if node.condition:
            cond_type = self._analyze_expression(node.condition)
            if cond_type and cond_type != 'bool':
                self._error(
                    f"For condition must be bool, got {cond_type}",
                    node.condition.line, node.condition.column
                )
        if node.update:
            self._analyze_statement(node.update)

        self._analyze_block(node.body)
        self.symbol_table.exit_scope()

    def _analyze_return(self, node: ReturnNode):
        """Analyze a return statement."""
        if not self.current_function:
            self._error("Return statement outside function", node.line, node.column)
            return

        expected = self.current_function.return_type

        if node.value:
            actual = self._analyze_expression(node.value)
            if actual and expected == 'void':
                self._error(
                    "Cannot return a value from void function",
                    node.line, node.column
                )
            elif actual and actual != expected:
                if not (expected == 'float' and actual == 'int'):
                    self._error(
                        f"Expected return type {expected}, got {actual}",
                        node.line, node.column
                    )
        elif expected != 'void':
            self._error(
                f"Function '{self.current_function.name}' must return {expected}",
                node.line, node.column
            )

    def _analyze_print(self, node: PrintNode):
        """Analyze a print statement."""
        self._analyze_expression(node.value)

    # ──────────────────────────── EXPRESSION ANALYSIS ──────────────────────────

    def _analyze_expression(self, node: ASTNode) -> Optional[str]:
        """
        Analyze an expression and return its resolved type.
        Also annotates the node with resolved_type.
        """
        result_type = None

        if isinstance(node, NumberNode):
            result_type = 'float' if isinstance(node.value, float) else 'int'

        elif isinstance(node, StringNode):
            result_type = 'string'

        elif isinstance(node, BoolNode):
            result_type = 'bool'

        elif isinstance(node, IdentifierNode):
            sym = self.symbol_table.lookup(node.name)
            if not sym:
                self._error(
                    f"Undefined variable: '{node.name}'",
                    node.line, node.column
                )
            else:
                result_type = sym.type

        elif isinstance(node, BinaryOpNode):
            result_type = self._analyze_binary_op(node)

        elif isinstance(node, UnaryOpNode):
            result_type = self._analyze_unary_op(node)

        elif isinstance(node, FunctionCallNode):
            result_type = self._analyze_function_call(node)

        elif isinstance(node, ArrayAccessNode):
            result_type = self._analyze_array_access(node)

        elif isinstance(node, InputNode):
            result_type = 'string'

        node.resolved_type = result_type
        return result_type

    def _analyze_binary_op(self, node: BinaryOpNode) -> Optional[str]:
        """Analyze a binary operation and return the result type."""
        left_type = self._analyze_expression(node.left)
        right_type = self._analyze_expression(node.right)

        if not left_type or not right_type:
            return None

        # Arithmetic operators: +, -, *, /, %
        if node.op in ('+', '-', '*', '/', '%'):
            if left_type == 'string' and right_type == 'string' and node.op == '+':
                return 'string'  # String concatenation
            if left_type in ('int', 'float') and right_type in ('int', 'float'):
                if node.op == '/':
                    return 'float'  # Division always returns float
                return 'float' if 'float' in (left_type, right_type) else 'int'
            self._error(
                f"Cannot apply '{node.op}' to {left_type} and {right_type}",
                node.line, node.column
            )
            return None

        # Comparison operators: ==, !=, <, >, <=, >=
        if node.op in ('==', '!=', '<', '>', '<=', '>='):
            if left_type in ('int', 'float') and right_type in ('int', 'float'):
                return 'bool'
            if left_type == right_type and node.op in ('==', '!='):
                return 'bool'  # Equality works for same types
            self._error(
                f"Cannot compare {left_type} and {right_type} with '{node.op}'",
                node.line, node.column
            )
            return None

        # Logical operators: and, or
        if node.op in ('and', 'or'):
            if left_type == 'bool' and right_type == 'bool':
                return 'bool'
            self._error(
                f"Logical '{node.op}' requires bool operands, got {left_type} and {right_type}",
                node.line, node.column
            )
            return None

        return None

    def _analyze_unary_op(self, node: UnaryOpNode) -> Optional[str]:
        """Analyze a unary operation and return the result type."""
        operand_type = self._analyze_expression(node.operand)
        if not operand_type:
            return None

        if node.op == '-':
            if operand_type in ('int', 'float'):
                return operand_type
            self._error(
                f"Cannot negate {operand_type}",
                node.line, node.column
            )
            return None

        if node.op == 'not':
            if operand_type == 'bool':
                return 'bool'
            self._error(
                f"'not' requires bool operand, got {operand_type}",
                node.line, node.column
            )
            return None

        return None

    def _analyze_function_call(self, node: FunctionCallNode) -> Optional[str]:
        """Analyze a function call and return the return type."""
        sym = self.symbol_table.lookup(node.name)
        if not sym:
            self._error(
                f"Undefined function: '{node.name}'",
                node.line, node.column
            )
            return None

        if sym.kind != 'function':
            self._error(
                f"'{node.name}' is not a function",
                node.line, node.column
            )
            return None

        # Check argument count
        if len(node.arguments) != len(sym.params):
            self._error(
                f"Function '{node.name}' expects {len(sym.params)} arguments, "
                f"got {len(node.arguments)}",
                node.line, node.column
            )
            return sym.return_type

        # Check argument types
        for i, (arg, expected_type) in enumerate(zip(node.arguments, sym.params)):
            arg_type = self._analyze_expression(arg)
            if arg_type and arg_type != expected_type:
                if not (expected_type == 'float' and arg_type == 'int'):
                    self._error(
                        f"Argument {i + 1} of '{node.name}': expected {expected_type}, got {arg_type}",
                        arg.line, arg.column
                    )

        return sym.return_type

    def _analyze_array_access(self, node: ArrayAccessNode) -> Optional[str]:
        """Analyze an array access and return the element type."""
        array_type = self._analyze_expression(node.array)
        index_type = self._analyze_expression(node.index)

        if index_type and index_type != 'int':
            self._error(
                f"Array index must be int, got {index_type}",
                node.index.line, node.index.column
            )

        return array_type  # Element type is the base type
