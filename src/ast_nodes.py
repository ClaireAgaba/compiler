"""
MiniLang Compiler — AST Node Definitions
==========================================
Defines the Abstract Syntax Tree (AST) node hierarchy.
The parser produces these nodes; the semantic analyzer annotates them;
the IR generator traverses them to produce Three-Address Code.

Every node stores source location (line, column) for error reporting.
Each node has a pretty_print() method for visualization.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any


# ═══════════════════════════════════════════════════════════════════════════════
#  BASE NODE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    line: int = 0
    column: int = 0
    # Annotated by semantic analyzer:
    resolved_type: Optional[str] = field(default=None, repr=False)

    def pretty_print(self, indent: int = 0) -> str:
        """Return a human-readable tree representation."""
        return "  " * indent + self.__class__.__name__


# ═══════════════════════════════════════════════════════════════════════════════
#  PROGRAM (ROOT)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ProgramNode(ASTNode):
    """Root node: a program is a list of function declarations."""
    functions: List['FunctionNode'] = field(default_factory=list)

    def pretty_print(self, indent=0):
        lines = ["  " * indent + "Program"]
        for func in self.functions:
            lines.append(func.pretty_print(indent + 1))
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  DECLARATIONS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ParamNode(ASTNode):
    """Function parameter: name and type."""
    name: str = ""
    param_type: str = ""

    def pretty_print(self, indent=0):
        return "  " * indent + f"Param({self.name}: {self.param_type})"


@dataclass
class FunctionNode(ASTNode):
    """Function declaration with name, params, return type, and body."""
    name: str = ""
    params: List[ParamNode] = field(default_factory=list)
    return_type: str = ""
    body: 'BlockNode' = None

    def pretty_print(self, indent=0):
        params_str = ", ".join(f"{p.name}:{p.param_type}" for p in self.params)
        lines = ["  " * indent + f"Function {self.name}({params_str}) -> {self.return_type}"]
        if self.body:
            lines.append(self.body.pretty_print(indent + 1))
        return "\n".join(lines)


@dataclass
class VarDeclNode(ASTNode):
    """Variable declaration: var name: type = initializer;"""
    name: str = ""
    var_type: str = ""
    initializer: Optional[ASTNode] = None
    array_size: Optional[int] = None   # For array declarations: int[10]

    def pretty_print(self, indent=0):
        type_str = self.var_type
        if self.array_size is not None:
            type_str += f"[{self.array_size}]"
        line = "  " * indent + f"VarDecl({self.name}: {type_str})"
        if self.initializer:
            line += "\n" + "  " * (indent + 1) + "= " + self.initializer.pretty_print(0)
        return line


# ═══════════════════════════════════════════════════════════════════════════════
#  STATEMENTS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BlockNode(ASTNode):
    """A block of statements: { ... }"""
    statements: List[ASTNode] = field(default_factory=list)

    def pretty_print(self, indent=0):
        lines = ["  " * indent + "Block"]
        for stmt in self.statements:
            lines.append(stmt.pretty_print(indent + 1))
        return "\n".join(lines)


@dataclass
class IfNode(ASTNode):
    """If statement: if (condition) { then_block } else { else_block }"""
    condition: ASTNode = None
    then_block: BlockNode = None
    else_block: Optional[BlockNode] = None

    def pretty_print(self, indent=0):
        lines = ["  " * indent + "If"]
        lines.append("  " * (indent + 1) + "Condition:")
        lines.append(self.condition.pretty_print(indent + 2))
        lines.append("  " * (indent + 1) + "Then:")
        lines.append(self.then_block.pretty_print(indent + 2))
        if self.else_block:
            lines.append("  " * (indent + 1) + "Else:")
            lines.append(self.else_block.pretty_print(indent + 2))
        return "\n".join(lines)


@dataclass
class WhileNode(ASTNode):
    """While loop: while (condition) { body }"""
    condition: ASTNode = None
    body: BlockNode = None

    def pretty_print(self, indent=0):
        lines = ["  " * indent + "While"]
        lines.append("  " * (indent + 1) + "Condition:")
        lines.append(self.condition.pretty_print(indent + 2))
        lines.append("  " * (indent + 1) + "Body:")
        lines.append(self.body.pretty_print(indent + 2))
        return "\n".join(lines)


@dataclass
class ForNode(ASTNode):
    """For loop: for (init; condition; update) { body }"""
    init: Optional[ASTNode] = None
    condition: Optional[ASTNode] = None
    update: Optional[ASTNode] = None
    body: BlockNode = None

    def pretty_print(self, indent=0):
        lines = ["  " * indent + "For"]
        if self.init:
            lines.append("  " * (indent + 1) + "Init:")
            lines.append(self.init.pretty_print(indent + 2))
        if self.condition:
            lines.append("  " * (indent + 1) + "Condition:")
            lines.append(self.condition.pretty_print(indent + 2))
        if self.update:
            lines.append("  " * (indent + 1) + "Update:")
            lines.append(self.update.pretty_print(indent + 2))
        lines.append("  " * (indent + 1) + "Body:")
        lines.append(self.body.pretty_print(indent + 2))
        return "\n".join(lines)


@dataclass
class ReturnNode(ASTNode):
    """Return statement: return expr;"""
    value: Optional[ASTNode] = None

    def pretty_print(self, indent=0):
        line = "  " * indent + "Return"
        if self.value:
            line += "\n" + self.value.pretty_print(indent + 1)
        return line


@dataclass
class PrintNode(ASTNode):
    """Print statement: print(expr);"""
    value: ASTNode = None

    def pretty_print(self, indent=0):
        lines = ["  " * indent + "Print"]
        lines.append(self.value.pretty_print(indent + 1))
        return "\n".join(lines)


@dataclass
class AssignNode(ASTNode):
    """Assignment: target = value; (target can be identifier or array access)"""
    target: ASTNode = None
    value: ASTNode = None

    def pretty_print(self, indent=0):
        lines = ["  " * indent + "Assign"]
        lines.append("  " * (indent + 1) + "Target:")
        lines.append(self.target.pretty_print(indent + 2))
        lines.append("  " * (indent + 1) + "Value:")
        lines.append(self.value.pretty_print(indent + 2))
        return "\n".join(lines)


@dataclass
class ExprStmtNode(ASTNode):
    """Expression used as a statement (e.g., function call)."""
    expression: ASTNode = None

    def pretty_print(self, indent=0):
        lines = ["  " * indent + "ExprStmt"]
        lines.append(self.expression.pretty_print(indent + 1))
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  EXPRESSIONS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BinaryOpNode(ASTNode):
    """Binary operation: left OP right"""
    op: str = ""
    left: ASTNode = None
    right: ASTNode = None

    def pretty_print(self, indent=0):
        lines = ["  " * indent + f"BinaryOp({self.op})"]
        lines.append(self.left.pretty_print(indent + 1))
        lines.append(self.right.pretty_print(indent + 1))
        return "\n".join(lines)


@dataclass
class UnaryOpNode(ASTNode):
    """Unary operation: OP operand"""
    op: str = ""
    operand: ASTNode = None

    def pretty_print(self, indent=0):
        lines = ["  " * indent + f"UnaryOp({self.op})"]
        lines.append(self.operand.pretty_print(indent + 1))
        return "\n".join(lines)


@dataclass
class NumberNode(ASTNode):
    """Numeric literal (int or float)."""
    value: Any = 0

    def pretty_print(self, indent=0):
        return "  " * indent + f"Number({self.value})"


@dataclass
class StringNode(ASTNode):
    """String literal."""
    value: str = ""

    def pretty_print(self, indent=0):
        return "  " * indent + f'String("{self.value}")'


@dataclass
class BoolNode(ASTNode):
    """Boolean literal."""
    value: bool = False

    def pretty_print(self, indent=0):
        return "  " * indent + f"Bool({self.value})"


@dataclass
class IdentifierNode(ASTNode):
    """Variable or function name reference."""
    name: str = ""

    def pretty_print(self, indent=0):
        return "  " * indent + f"Identifier({self.name})"


@dataclass
class FunctionCallNode(ASTNode):
    """Function call: name(args)"""
    name: str = ""
    arguments: List[ASTNode] = field(default_factory=list)

    def pretty_print(self, indent=0):
        lines = ["  " * indent + f"FunctionCall({self.name})"]
        for arg in self.arguments:
            lines.append(arg.pretty_print(indent + 1))
        return "\n".join(lines)


@dataclass
class ArrayAccessNode(ASTNode):
    """Array index access: array[index]"""
    array: ASTNode = None
    index: ASTNode = None

    def pretty_print(self, indent=0):
        lines = ["  " * indent + "ArrayAccess"]
        lines.append(self.array.pretty_print(indent + 1))
        lines.append("  " * (indent + 1) + "Index:")
        lines.append(self.index.pretty_print(indent + 2))
        return "\n".join(lines)


@dataclass
class InputNode(ASTNode):
    """Input expression: input()"""

    def pretty_print(self, indent=0):
        return "  " * indent + "Input()"
