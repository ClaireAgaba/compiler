import unittest

from src.compiler import Compiler


def compile_source(source: str):
    compiler = Compiler()
    return compiler.compile_step_by_step(source)


class OptimizerTests(unittest.TestCase):
    def test_multiply_by_one_and_alias_chain_are_simplified(self):
        source = """
func main() -> void {
    var x: int = 1;
    var a: int = x * 1;
    var b: int = a;
}
"""
        stages = compile_source(source)
        optimized = [repr(instr).strip() for instr in stages['optimized_tac']]

        self.assertNotIn("t0 = 1", optimized)
        self.assertIn("x = 1", optimized)
        self.assertIn("a = 1", optimized)
        self.assertIn("b = 1", optimized)

    def test_identity_rules_keep_non_identity_operand(self):
        source = """
func main() -> void {
    var x: int = input();
    var a: int = x * 1;
    var b: int = 0 + a;
    print(b);
}
"""
        stages = compile_source(source)
        optimized = [repr(instr).strip() for instr in stages['optimized_tac']]

        self.assertFalse(any(" * 1" in instr for instr in optimized))
        self.assertFalse(any("0 +" in instr for instr in optimized))
        self.assertTrue(any(instr.startswith("a = ") for instr in optimized))
        self.assertTrue(any(instr.startswith("b = ") for instr in optimized))


if __name__ == "__main__":
    unittest.main()