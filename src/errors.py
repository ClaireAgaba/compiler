"""
MiniLang Compiler — Error Handling
===================================
Unified error classes for all compiler stages.
Every error carries line/column info for precise diagnostics.
"""


class CompilerError(Exception):
    """Base class for all compiler errors."""

    def __init__(self, message, line=None, column=None):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self.format())

    def format(self):
        location = ""
        if self.line is not None:
            location = f" [line {self.line}"
            if self.column is not None:
                location += f", col {self.column}"
            location += "]"
        return f"{self.__class__.__name__}{location}: {self.message}"


class LexerError(CompilerError):
    """Raised during lexical analysis."""
    pass


class ParseError(CompilerError):
    """Raised during parsing."""
    pass


class SemanticError(CompilerError):
    """Raised during semantic analysis."""
    pass


class IRError(CompilerError):
    """Raised during intermediate code generation."""
    pass


class OptimizerError(CompilerError):
    """Raised during optimization."""
    pass


class CodeGenError(CompilerError):
    """Raised during code generation."""
    pass


class VMError(CompilerError):
    """Raised during VM execution (runtime error)."""
    pass
