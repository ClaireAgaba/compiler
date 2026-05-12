"""
MiniLang Compiler — Symbol Table
==================================
Scoped symbol table using a stack of hash maps.
Used by the Semantic Analyzer for name resolution and type checking.

Each scope level is a dictionary mapping names to Symbol objects.
Lookup searches from the innermost scope outward (lexical scoping).
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class Symbol:
    """
    A single symbol in the symbol table.

    Attributes:
        name:        The identifier name.
        type:        The type string ('int', 'float', 'bool', 'string', 'void').
        kind:        'variable', 'parameter', or 'function'.
        scope_level: The nesting level where this symbol was defined.
        params:      For functions: list of parameter types.
        return_type: For functions: the return type.
        array_size:  For arrays: the declared size.
    """
    name: str
    type: str
    kind: str  # 'variable', 'parameter', 'function'
    scope_level: int = 0
    params: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    array_size: Optional[int] = None

    def __repr__(self):
        base = f"Symbol({self.name}: {self.type}, {self.kind}, level={self.scope_level})"
        if self.kind == 'function':
            params_str = ", ".join(self.params)
            base = f"Symbol({self.name}({params_str}) -> {self.return_type}, level={self.scope_level})"
        return base


class SymbolTable:
    """
    Scoped symbol table implementing lexical (static) scoping.

    Uses a stack of dictionaries. Each dictionary represents one scope level.
    The bottom of the stack is the global scope; each new block pushes a new scope.

    Example:
        table = SymbolTable()
        table.define("x", "int", "variable")
        table.enter_scope()
        table.define("y", "float", "variable")
        sym = table.lookup("x")  # Finds x from the outer scope
        table.exit_scope()
    """

    def __init__(self):
        # Stack of scopes: each scope is a dict[name -> Symbol]
        self.scopes: List[Dict[str, Symbol]] = [{}]  # Start with global scope
        self.scope_level = 0

    def enter_scope(self):
        """Push a new scope onto the stack."""
        self.scope_level += 1
        self.scopes.append({})

    def exit_scope(self):
        """Pop the current scope from the stack."""
        if self.scope_level > 0:
            self.scopes.pop()
            self.scope_level -= 1

    def define(self, name: str, sym_type: str, kind: str,
               params: List[str] = None, return_type: str = None,
               array_size: int = None) -> Symbol:
        """
        Define a new symbol in the CURRENT (innermost) scope.

        Args:
            name: Identifier name.
            sym_type: Type of the symbol.
            kind: 'variable', 'parameter', or 'function'.
            params: For functions, list of parameter type strings.
            return_type: For functions, the return type.
            array_size: For arrays, the declared size.

        Returns:
            The newly created Symbol.

        Raises:
            ValueError if the name is already defined in the current scope.
        """
        current_scope = self.scopes[-1]
        if name in current_scope:
            raise ValueError(f"Symbol '{name}' already defined in current scope")

        symbol = Symbol(
            name=name,
            type=sym_type,
            kind=kind,
            scope_level=self.scope_level,
            params=params or [],
            return_type=return_type,
            array_size=array_size,
        )
        current_scope[name] = symbol
        return symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        """
        Look up a symbol by name, searching from innermost to outermost scope.
        Returns the Symbol if found, or None if not found.
        """
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def lookup_current_scope(self, name: str) -> Optional[Symbol]:
        """Look up a symbol only in the current (innermost) scope."""
        return self.scopes[-1].get(name)

    def get_all_symbols(self) -> List[Symbol]:
        """Return all symbols across all scopes (for visualization)."""
        all_symbols = []
        for scope in self.scopes:
            all_symbols.extend(scope.values())
        return all_symbols

    def pretty_print(self) -> str:
        """Return a human-readable representation of the symbol table."""
        lines = ["Symbol Table:"]
        lines.append("=" * 60)
        for i, scope in enumerate(self.scopes):
            scope_name = "Global" if i == 0 else f"Scope Level {i}"
            lines.append(f"\n  [{scope_name}]")
            if not scope:
                lines.append("    (empty)")
            for name, sym in scope.items():
                lines.append(f"    {sym}")
        lines.append("=" * 60)
        return "\n".join(lines)
