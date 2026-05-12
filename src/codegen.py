"""
MiniLang Compiler — Stage 6: Bytecode Code Generator
======================================================
Translates optimized Three-Address Code (TAC) into bytecode
instructions for the stack-based Virtual Machine.

The bytecode is a list of (opcode, operand) tuples that the VM executes.
"""

from typing import List, Dict, Tuple, Any, Optional
from .ir_generator import TACInstruction
from .errors import CodeGenError
from enum import Enum, auto


class OpCode(Enum):
    """Bytecode operation codes for the stack-based VM."""
    PUSH = auto()       # Push constant onto stack
    POP = auto()        # Pop top of stack
    LOAD = auto()       # Load variable value onto stack
    STORE = auto()      # Pop and store into variable
    ADD = auto()        # Pop 2, push sum
    SUB = auto()        # Pop 2, push difference
    MUL = auto()        # Pop 2, push product
    DIV = auto()        # Pop 2, push quotient
    MOD = auto()        # Pop 2, push remainder
    NEG = auto()        # Negate top of stack
    EQ = auto()         # Pop 2, push ==
    NE = auto()         # Pop 2, push !=
    LT = auto()         # Pop 2, push <
    GT = auto()         # Pop 2, push >
    LE = auto()         # Pop 2, push <=
    GE = auto()         # Pop 2, push >=
    AND = auto()        # Logical AND
    OR = auto()         # Logical OR
    NOT = auto()        # Logical NOT
    JMP = auto()        # Unconditional jump
    JZ = auto()         # Jump if zero/false
    JNZ = auto()        # Jump if non-zero/true
    CALL = auto()       # Function call
    RET = auto()        # Return from function
    PRINT = auto()      # Print top of stack
    INPUT = auto()      # Read input, push onto stack
    ALOAD = auto()      # Array load
    ASTORE = auto()     # Array store
    ALLOC = auto()      # Allocate array
    HALT = auto()       # Stop execution


class BytecodeInstruction:
    """A single bytecode instruction with opcode and optional operand."""
    def __init__(self, opcode: OpCode, operand: Any = None):
        self.opcode = opcode
        self.operand = operand

    def __repr__(self):
        if self.operand is not None:
            return f"{self.opcode.name} {self.operand}"
        return f"{self.opcode.name}"


class CodeGenerator:
    """
    Bytecode Code Generator for MiniLang.
    
    Translates TAC into stack-based bytecode instructions.
    
    Usage:
        codegen = CodeGenerator()
        bytecode = codegen.generate(tac_instructions)
    """

    def __init__(self):
        self.bytecode: List[BytecodeInstruction] = []
        self.labels: Dict[str, int] = {}        # label -> bytecode address
        self.pending_jumps: List[Tuple[int, str]] = []  # (bytecode_index, label)
        self.functions: Dict[str, int] = {}      # function_name -> bytecode address

    def generate(self, tac: List[TACInstruction]) -> List[BytecodeInstruction]:
        """Generate bytecode from TAC instructions."""
        self.bytecode = []
        self.labels = {}
        self.pending_jumps = []
        self.functions = {}

        # First pass: generate bytecode
        for instr in tac:
            self._translate(instr)

        # Add HALT at the end
        self._emit(OpCode.HALT)

        # Second pass: resolve jump targets
        self._resolve_jumps()

        return self.bytecode

    def _emit(self, opcode: OpCode, operand: Any = None) -> int:
        """Emit a bytecode instruction and return its index."""
        idx = len(self.bytecode)
        self.bytecode.append(BytecodeInstruction(opcode, operand))
        return idx

    def _translate(self, instr: TACInstruction):
        """Translate a single TAC instruction to bytecode."""

        if instr.op == 'FUNC_BEGIN':
            self.functions[instr.arg1] = len(self.bytecode)
            self.labels[f"__func_{instr.arg1}"] = len(self.bytecode)

        elif instr.op == 'FUNC_END':
            pass  # No-op; return handled by RETURN

        elif instr.op == 'PARAM' and instr.result:
            # Parameter declaration (in function header) — store incoming arg
            self._emit(OpCode.STORE, instr.result)

        elif instr.op == 'PARAM' and not instr.result:
            # Pushing argument for a function call
            self._push_value(instr.arg1)

        elif instr.op == 'LABEL':
            self.labels[instr.label] = len(self.bytecode)

        elif instr.op == 'GOTO':
            idx = self._emit(OpCode.JMP, None)
            self.pending_jumps.append((idx, instr.label))

        elif instr.op == 'IF_FALSE':
            self._push_value(instr.arg1)
            idx = self._emit(OpCode.JZ, None)
            self.pending_jumps.append((idx, instr.label))

        elif instr.op == 'IF_TRUE':
            self._push_value(instr.arg1)
            idx = self._emit(OpCode.JNZ, None)
            self.pending_jumps.append((idx, instr.label))

        elif instr.op == 'ASSIGN':
            self._push_value(instr.arg1)
            self._emit(OpCode.STORE, instr.result)

        elif instr.op in ('+', '-', '*', '/', '%'):
            op_map = {'+': OpCode.ADD, '-': OpCode.SUB, '*': OpCode.MUL,
                      '/': OpCode.DIV, '%': OpCode.MOD}
            self._push_value(instr.arg1)
            self._push_value(instr.arg2)
            self._emit(op_map[instr.op])
            self._emit(OpCode.STORE, instr.result)

        elif instr.op in ('==', '!=', '<', '>', '<=', '>='):
            op_map = {'==': OpCode.EQ, '!=': OpCode.NE, '<': OpCode.LT,
                      '>': OpCode.GT, '<=': OpCode.LE, '>=': OpCode.GE}
            self._push_value(instr.arg1)
            self._push_value(instr.arg2)
            self._emit(op_map[instr.op])
            self._emit(OpCode.STORE, instr.result)

        elif instr.op in ('and', 'or'):
            op_map = {'and': OpCode.AND, 'or': OpCode.OR}
            self._push_value(instr.arg1)
            self._push_value(instr.arg2)
            self._emit(op_map[instr.op])
            self._emit(OpCode.STORE, instr.result)

        elif instr.op == 'NEG':
            self._push_value(instr.arg1)
            self._emit(OpCode.NEG)
            self._emit(OpCode.STORE, instr.result)

        elif instr.op == 'NOT':
            self._push_value(instr.arg1)
            self._emit(OpCode.NOT)
            self._emit(OpCode.STORE, instr.result)

        elif instr.op == 'CALL':
            idx = self._emit(OpCode.CALL, (instr.arg1, instr.arg2))
            self._emit(OpCode.STORE, instr.result)

        elif instr.op == 'RETURN':
            if instr.arg1 is not None:
                self._push_value(instr.arg1)
            self._emit(OpCode.RET)

        elif instr.op == 'PRINT':
            self._push_value(instr.arg1)
            self._emit(OpCode.PRINT)

        elif instr.op == 'INPUT':
            self._emit(OpCode.INPUT)
            self._emit(OpCode.STORE, instr.result)

        elif instr.op == 'ARRAY_ALLOC':
            self._emit(OpCode.ALLOC, (instr.result, instr.arg1))

        elif instr.op == 'ARRAY_LOAD':
            self._push_value(instr.arg1)
            self._push_value(instr.arg2)
            self._emit(OpCode.ALOAD)
            self._emit(OpCode.STORE, instr.result)

        elif instr.op == 'ARRAY_STORE':
            self._push_value(instr.result)  # array name
            self._push_value(instr.arg1)    # index
            self._push_value(instr.arg2)    # value
            self._emit(OpCode.ASTORE)

    def _push_value(self, value):
        """Push a value onto the stack — either a literal or a variable load."""
        if value is None:
            self._emit(OpCode.PUSH, 0)
            return

        s = str(value)

        # Boolean
        if s == 'true':
            self._emit(OpCode.PUSH, True)
        elif s == 'false':
            self._emit(OpCode.PUSH, False)
        # String literal
        elif s.startswith('"') and s.endswith('"'):
            self._emit(OpCode.PUSH, s[1:-1])
        # Number
        elif self._is_number(s):
            if '.' in s:
                self._emit(OpCode.PUSH, float(s))
            else:
                self._emit(OpCode.PUSH, int(s))
        # Variable
        else:
            self._emit(OpCode.LOAD, s)

    def _resolve_jumps(self):
        """Resolve all pending jump targets to actual bytecode addresses."""
        for idx, label in self.pending_jumps:
            if label in self.labels:
                self.bytecode[idx].operand = self.labels[label]
            else:
                raise CodeGenError(f"Undefined label: {label}")

    @staticmethod
    def _is_number(s: str) -> bool:
        try:
            float(s)
            return True
        except (ValueError, TypeError):
            return False
