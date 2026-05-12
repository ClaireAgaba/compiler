import unittest

from src.compiler import Compiler
from src.errors import SemanticError


def compile_source(source: str):
    compiler = Compiler()
    return compiler.compile_step_by_step(source)


class SemanticAnalysisTests(unittest.TestCase):
    def assert_semantic_error_contains(self, source: str, expected: str):
        with self.assertRaises(SemanticError) as ctx:
            compile_source(source)
        self.assertIn(expected, str(ctx.exception))

    def test_undeclared_identifier(self):
        source = """
func main() -> void {
    print(y);
}
"""
        self.assert_semantic_error_contains(source, "Undefined variable")

    def test_duplicate_declaration_same_scope(self):
        source = """
func main() -> void {
    var x: int = 1;
    var x: int = 2;
}
"""
        self.assert_semantic_error_contains(source, "already defined in this scope")

    def test_type_mismatch_assignment(self):
        source = """
func main() -> void {
    var a: int = \"hello\";
}
"""
        self.assert_semantic_error_contains(source, "Cannot assign string")

    def test_wrong_argument_count(self):
        source = """
func add(a: int, b: int) -> int {
    return a + b;
}

func main() -> void {
    print(add(1));
}
"""
        self.assert_semantic_error_contains(source, "expects 2 arguments")

    def test_wrong_argument_type(self):
        source = """
func add(a: int, b: int) -> int {
    return a + b;
}

func main() -> void {
    print(add(1, true));
}
"""
        self.assert_semantic_error_contains(source, "expected int, got bool")

    def test_invalid_return_type(self):
        source = """
func bad() -> int {
    return true;
}

func main() -> void {
    print(0);
}
"""
        self.assert_semantic_error_contains(source, "Expected return type int, got bool")

    def test_scope_shadowing_is_allowed(self):
        source = """
func main() -> void {
    var x: int = 1;
    if (true) {
        var x: int = 2;
        print(x);
    }
    print(x);
}
"""
        stages = compile_source(source)
        self.assertIn("symbol_table", stages)


if __name__ == "__main__":
    unittest.main()
