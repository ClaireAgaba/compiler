"""
MiniLang Compiler — Stage 5: Code Optimizer
=============================================
Implements multiple optimization passes on Three-Address Code (TAC).

Passes:
  1. Constant Folding — evaluate 3 + 5 → 8 at compile time
  2. Constant Propagation — if x = 5, replace uses of x with 5
  3. Dead Code Elimination — remove instructions whose results are never used
  4. Common Subexpression Elimination — reuse a + b if already computed
  5. Strength Reduction — replace x * 2 with x + x
"""

from typing import List, Dict, Set, Tuple
from .ir_generator import TACInstruction
import copy


class Optimizer:
    """
    TAC Optimizer — applies multiple optimization passes.
    
    Usage:
        optimizer = Optimizer()
        optimized_tac, report = optimizer.optimize(tac_instructions)
    """

    def __init__(self):
        self.report: List[str] = []

    def optimize(self, instructions: List[TACInstruction]) -> Tuple[List[TACInstruction], List[str]]:
        """Apply all optimization passes and return (optimized_tac, report)."""
        self.report = []
        result = copy.deepcopy(instructions)

        original_count = len(result)

        result = self._constant_folding(result)
        result = self._constant_propagation(result)
        result = self._strength_reduction(result)
        result = self._dead_code_elimination(result)
        result = self._common_subexpression_elimination(result)

        self.report.append(f"Total: {original_count} → {len(result)} instructions")
        return result, self.report

    def _constant_folding(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Evaluate constant expressions at compile time."""
        count = 0
        ops = {
            '+': lambda a, b: a + b, '-': lambda a, b: a - b,
            '*': lambda a, b: a * b, '/': lambda a, b: a / b if b != 0 else None,
            '%': lambda a, b: a % b if b != 0 else None,
            '<': lambda a, b: a < b, '>': lambda a, b: a > b,
            '<=': lambda a, b: a <= b, '>=': lambda a, b: a >= b,
            '==': lambda a, b: a == b, '!=': lambda a, b: a != b,
        }

        for instr in instructions:
            if instr.op in ops and instr.arg1 is not None and instr.arg2 is not None:
                try:
                    a = self._try_numeric(instr.arg1)
                    b = self._try_numeric(instr.arg2)
                    if a is not None and b is not None:
                        result = ops[instr.op](a, b)
                        if result is not None:
                            if isinstance(result, bool):
                                instr.arg1 = str(result).lower()
                            elif isinstance(result, float) and result == int(result):
                                instr.arg1 = str(int(result))
                            else:
                                instr.arg1 = str(result)
                            instr.arg2 = None
                            instr.op = 'ASSIGN'
                            count += 1
                except (ValueError, ZeroDivisionError, TypeError):
                    pass

        self.report.append(f"Constant Folding: {count} expressions folded")
        return instructions

    def _constant_propagation(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """If x = constant, replace later uses of x with the constant."""
        count = 0
        constants: Dict[str, str] = {}

        for instr in instructions:
            # Track constant assignments
            if instr.op == 'ASSIGN' and instr.result and instr.arg1 is not None:
                val = str(instr.arg1)
                if self._try_numeric(val) is not None or val in ('true', 'false'):
                    constants[instr.result] = val
                elif val in constants:
                    constants[instr.result] = constants[val]
                else:
                    constants.pop(instr.result, None)
            elif instr.result:
                constants.pop(instr.result, None)

            # Invalidate on labels/jumps (conservative)
            if instr.op in ('LABEL', 'FUNC_BEGIN'):
                constants.clear()

            # Replace uses of known constants
            if instr.op not in ('LABEL', 'GOTO', 'FUNC_BEGIN', 'FUNC_END', 'ASSIGN'):
                if instr.arg1 and str(instr.arg1) in constants:
                    instr.arg1 = constants[str(instr.arg1)]
                    count += 1
                if instr.arg2 and str(instr.arg2) in constants:
                    instr.arg2 = constants[str(instr.arg2)]
                    count += 1

        self.report.append(f"Constant Propagation: {count} replacements")
        return instructions

    def _dead_code_elimination(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Remove instructions whose results are never used."""
        # Find all used variables
        used: Set[str] = set()
        for instr in instructions:
            if instr.arg1 and isinstance(instr.arg1, str) and not self._is_literal(instr.arg1):
                used.add(instr.arg1)
            if instr.arg2 and isinstance(instr.arg2, str) and not self._is_literal(str(instr.arg2)):
                used.add(str(instr.arg2))

        # Remove assignments to unused temporaries
        keep_ops = {'LABEL', 'GOTO', 'IF_FALSE', 'IF_TRUE', 'RETURN', 'PRINT',
                     'FUNC_BEGIN', 'FUNC_END', 'CALL', 'PARAM', 'INPUT',
                     'ARRAY_STORE'}
        result = []
        count = 0

        for instr in instructions:
            if instr.op not in keep_ops and instr.result:
                # Only eliminate temporaries (t0, t1, ...) that are never used
                if instr.result.startswith('t') and instr.result not in used:
                    count += 1
                    continue
            result.append(instr)

        self.report.append(f"Dead Code Elimination: {count} instructions removed")
        return result

    def _common_subexpression_elimination(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Reuse previously computed expressions."""
        count = 0
        computed: Dict[str, str] = {}  # "arg1 op arg2" -> result temp

        for instr in instructions:
            if instr.op in ('+', '-', '*', '/', '%', '<', '>', '<=', '>=', '==', '!='):
                key = f"{instr.arg1} {instr.op} {instr.arg2}"
                if key in computed:
                    instr.op = 'ASSIGN'
                    instr.arg1 = computed[key]
                    instr.arg2 = None
                    count += 1
                else:
                    computed[key] = instr.result

            # Invalidate on labels/jumps
            if instr.op in ('LABEL', 'FUNC_BEGIN', 'GOTO', 'IF_FALSE', 'IF_TRUE'):
                computed.clear()

        self.report.append(f"Common Subexpression Elimination: {count} reuses")
        return instructions

    def _strength_reduction(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Replace expensive operations with cheaper equivalents."""
        count = 0
        for instr in instructions:
            if instr.op == '*':
                val = self._try_numeric(instr.arg2)
                if val == 2:
                    instr.op = '+'
                    instr.arg2 = instr.arg1
                    count += 1
                elif val == 1:
                    instr.op = 'ASSIGN'
                    instr.arg2 = None
                    count += 1
                elif val == 0:
                    instr.op = 'ASSIGN'
                    instr.arg1 = '0'
                    instr.arg2 = None
                    count += 1
            elif instr.op == '+':
                if self._try_numeric(instr.arg2) == 0:
                    instr.op = 'ASSIGN'
                    instr.arg2 = None
                    count += 1
                elif self._try_numeric(instr.arg1) == 0:
                    instr.op = 'ASSIGN'
                    instr.arg1 = instr.arg2
                    instr.arg2 = None
                    count += 1

        self.report.append(f"Strength Reduction: {count} operations simplified")
        return instructions

    # ──────────────────────────── Utilities ────────────────────────────────────

    @staticmethod
    def _try_numeric(value) -> object:
        """Try to parse a value as a number. Returns None if not numeric."""
        if value is None:
            return None
        try:
            s = str(value)
            if '.' in s:
                return float(s)
            return int(s)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _is_literal(value: str) -> bool:
        """Check if a value is a literal (number, bool, string)."""
        if not value:
            return False
        if value in ('true', 'false'):
            return True
        if value.startswith('"'):
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False
