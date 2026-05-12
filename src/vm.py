"""
MiniLang Compiler — Stage 7: Virtual Machine (Runtime Environment)
===================================================================
Stack-based virtual machine that executes bytecode instructions.

Components:
  - Operand Stack — for expression evaluation
  - Call Stack — stack frames for function calls
  - Memory — variable storage (per-frame locals + globals)
  - Heap — array allocation
  - Instruction Pointer (IP) — current bytecode position

This serves as the "Runtime Environment" topic from the course.
"""

from typing import List, Dict, Any, Optional
from .codegen import BytecodeInstruction, OpCode
from .errors import VMError


class StackFrame:
    """
    A single call stack frame.

    Created on each function call; destroyed on return.
    Stores local variables, return address, and saved stack pointer.
    """
    def __init__(self, return_address: int, func_name: str = ""):
        self.return_address = return_address
        self.func_name = func_name
        self.locals: Dict[str, Any] = {}
        self.saved_sp: int = 0  # Stack pointer before call


class VM:
    """
    Stack-based Virtual Machine for MiniLang bytecode.

    Usage:
        vm = VM(bytecode, function_table)
        output = vm.run()
    """

    MAX_STEPS = 1_000_000  # Safety limit to prevent infinite loops

    def __init__(self, bytecode: List[BytecodeInstruction],
                 functions: Dict[str, int], trace: bool = False):
        self.bytecode = bytecode
        self.functions = functions   # function_name -> bytecode address
        self.trace = trace

        # VM state
        self.ip = 0                  # Instruction pointer
        self.stack: List[Any] = []   # Operand stack
        self.call_stack: List[StackFrame] = []  # Call stack
        self.globals: Dict[str, Any] = {}       # Global variables
        self.heap: Dict[str, List[Any]] = {}    # Arrays on the heap

        # Output capture
        self.output: List[str] = []
        self.trace_log: List[str] = []
        self.step_count = 0

        # Input queue (for non-interactive mode)
        self.input_queue: List[str] = []
        self.input_callback = None  # Optional callback for interactive input

    def run(self, inputs: List[str] = None) -> List[str]:
        """
        Execute the bytecode starting from main().

        Args:
            inputs: Pre-loaded input values for INPUT instructions.

        Returns:
            List of output strings from PRINT instructions.
        """
        if inputs:
            self.input_queue = list(inputs)

        # Find main() entry point
        if 'main' not in self.functions:
            raise VMError("No 'main' function found")

        # Set up initial frame for main
        self.ip = self.functions['main']
        self.call_stack.append(StackFrame(len(self.bytecode) - 1, "main"))

        # Execute
        while self.ip < len(self.bytecode):
            if self.step_count >= self.MAX_STEPS:
                raise VMError(f"Execution exceeded {self.MAX_STEPS} steps (infinite loop?)")

            instr = self.bytecode[self.ip]

            if self.trace:
                self._log_trace(instr)

            self.step_count += 1
            self.ip += 1  # Advance IP (jumps will override this)

            self._execute(instr)

            if instr.opcode == OpCode.HALT:
                break

        return self.output

    def run_step(self) -> Optional[Dict[str, Any]]:
        """
        Execute a single instruction and return the VM state.
        Used by the visualizer for step-by-step execution.
        """
        if self.ip >= len(self.bytecode):
            return None

        instr = self.bytecode[self.ip]
        state = {
            'ip': self.ip,
            'instruction': str(instr),
            'stack_before': list(self.stack),
            'halted': instr.opcode == OpCode.HALT,
        }

        self.ip += 1
        self._execute(instr)

        state['stack_after'] = list(self.stack)
        state['locals'] = dict(self.call_stack[-1].locals) if self.call_stack else {}
        state['globals'] = dict(self.globals)
        state['output'] = list(self.output)

        return state

    # ──────────────────────────── EXECUTION ENGINE ─────────────────────────────

    def _ensure_numeric_operand(self, value: Any, operation: str) -> Any:
        """Ensure an operand is numeric before arithmetic execution."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise VMError(
                f"Runtime input for '{operation}' must be a number. "
                f"Enter raw values like 7 or 3.5 in Runtime Inputs, not expressions like 'x*5-2' or '7-2'."
            )
        return value

    def _execute(self, instr: BytecodeInstruction):
        """Execute a single bytecode instruction."""
        op = instr.opcode

        if op == OpCode.PUSH:
            self.stack.append(instr.operand)

        elif op == OpCode.POP:
            self._pop()

        elif op == OpCode.LOAD:
            value = self._get_var(instr.operand)
            self.stack.append(value)

        elif op == OpCode.STORE:
            value = self._pop()
            self._set_var(instr.operand, value)

        elif op == OpCode.ADD:
            b, a = self._pop(), self._pop()
            if isinstance(a, str) or isinstance(b, str):
                self.stack.append(str(a) + str(b))
            else:
                self.stack.append(a + b)

        elif op == OpCode.SUB:
            b, a = self._pop(), self._pop()
            a = self._ensure_numeric_operand(a, '-')
            b = self._ensure_numeric_operand(b, '-')
            self.stack.append(a - b)

        elif op == OpCode.MUL:
            b, a = self._pop(), self._pop()
            a = self._ensure_numeric_operand(a, '*')
            b = self._ensure_numeric_operand(b, '*')
            self.stack.append(a * b)

        elif op == OpCode.DIV:
            b, a = self._pop(), self._pop()
            a = self._ensure_numeric_operand(a, '/')
            b = self._ensure_numeric_operand(b, '/')
            if b == 0:
                raise VMError("Division by zero")
            self.stack.append(a / b if isinstance(a, float) or isinstance(b, float) else a // b)

        elif op == OpCode.MOD:
            b, a = self._pop(), self._pop()
            a = self._ensure_numeric_operand(a, '%')
            b = self._ensure_numeric_operand(b, '%')
            if b == 0:
                raise VMError("Modulo by zero")
            self.stack.append(a % b)

        elif op == OpCode.NEG:
            a = self._pop()
            a = self._ensure_numeric_operand(a, 'unary -')
            self.stack.append(-a)

        elif op == OpCode.EQ:
            b, a = self._pop(), self._pop()
            self.stack.append(a == b)

        elif op == OpCode.NE:
            b, a = self._pop(), self._pop()
            self.stack.append(a != b)

        elif op == OpCode.LT:
            b, a = self._pop(), self._pop()
            self.stack.append(a < b)

        elif op == OpCode.GT:
            b, a = self._pop(), self._pop()
            self.stack.append(a > b)

        elif op == OpCode.LE:
            b, a = self._pop(), self._pop()
            self.stack.append(a <= b)

        elif op == OpCode.GE:
            b, a = self._pop(), self._pop()
            self.stack.append(a >= b)

        elif op == OpCode.AND:
            b, a = self._pop(), self._pop()
            self.stack.append(bool(a) and bool(b))

        elif op == OpCode.OR:
            b, a = self._pop(), self._pop()
            self.stack.append(bool(a) or bool(b))

        elif op == OpCode.NOT:
            a = self._pop()
            self.stack.append(not bool(a))

        elif op == OpCode.JMP:
            self.ip = instr.operand

        elif op == OpCode.JZ:
            cond = self._pop()
            if not cond or cond == 0 or cond is False:
                self.ip = instr.operand

        elif op == OpCode.JNZ:
            cond = self._pop()
            if cond and cond != 0 and cond is not False:
                self.ip = instr.operand

        elif op == OpCode.CALL:
            func_name, num_args = instr.operand
            self._call_function(func_name, num_args)

        elif op == OpCode.RET:
            self._return_function()

        elif op == OpCode.PRINT:
            value = self._pop()
            output_str = str(value)
            if isinstance(value, bool):
                output_str = str(value).lower()
            self.output.append(output_str)

        elif op == OpCode.INPUT:
            value = self._read_input()
            self.stack.append(value)

        elif op == OpCode.ALLOC:
            name, size = instr.operand
            self.heap[name] = [0] * size
            self._set_var(name, name)  # Store array reference

        elif op == OpCode.ALOAD:
            index = self._pop()
            array_ref = self._pop()
            arr_name = str(array_ref)
            if arr_name not in self.heap:
                raise VMError(f"Array '{arr_name}' not allocated")
            idx = int(index)
            if idx < 0 or idx >= len(self.heap[arr_name]):
                raise VMError(f"Array index {idx} out of bounds")
            self.stack.append(self.heap[arr_name][idx])

        elif op == OpCode.ASTORE:
            value = self._pop()
            index = self._pop()
            array_ref = self._pop()
            arr_name = str(array_ref)
            if arr_name not in self.heap:
                raise VMError(f"Array '{arr_name}' not allocated")
            idx = int(index)
            if idx < 0 or idx >= len(self.heap[arr_name]):
                raise VMError(f"Array index {idx} out of bounds")
            self.heap[arr_name][idx] = value

        elif op == OpCode.HALT:
            pass  # Handled in run loop

    # ──────────────────────────── VARIABLE ACCESS ──────────────────────────────

    def _get_var(self, name: str) -> Any:
        """Get a variable value, checking local scope first, then global."""
        if self.call_stack:
            frame = self.call_stack[-1]
            if name in frame.locals:
                return frame.locals[name]
        if name in self.globals:
            return self.globals[name]
        raise VMError(f"Undefined variable: '{name}'")

    def _set_var(self, name: str, value: Any):
        """Set a variable value in the current scope."""
        if self.call_stack:
            frame = self.call_stack[-1]
            # If already exists locally or globally, update the right one
            if name in frame.locals:
                frame.locals[name] = value
                return
            if name in self.globals:
                self.globals[name] = value
                return
            # New variable — define locally
            frame.locals[name] = value
        else:
            self.globals[name] = value

    # ──────────────────────────── FUNCTION CALLS ───────────────────────────────

    def _call_function(self, func_name: str, num_args: int):
        """Handle a function call."""
        if func_name not in self.functions:
            raise VMError(f"Undefined function: '{func_name}'")

        # Collect arguments from the stack (they were pushed by PARAM instructions)
        args = []
        for _ in range(num_args):
            args.insert(0, self._pop())

        # Create new stack frame
        frame = StackFrame(self.ip, func_name)
        frame.saved_sp = len(self.stack)
        self.call_stack.append(frame)

        # Push arguments back so the function's PARAM/STORE instructions can pop them
        for arg in args:
            self.stack.append(arg)

        # Jump to function
        self.ip = self.functions[func_name]

    def _return_function(self):
        """Handle a function return."""
        if not self.call_stack:
            raise VMError("Return outside of function")

        # Get return value if any
        return_value = None
        if self.stack:
            return_value = self._pop()

        frame = self.call_stack.pop()

        # Restore stack
        while len(self.stack) > frame.saved_sp:
            self.stack.pop()

        # Push return value
        if return_value is not None:
            self.stack.append(return_value)

        # Jump to return address
        self.ip = frame.return_address

    # ──────────────────────────── STACK OPERATIONS ─────────────────────────────

    def _pop(self) -> Any:
        """Pop and return top of stack."""
        if not self.stack:
            raise VMError("Stack underflow")
        return self.stack.pop()

    # ──────────────────────────── I/O ──────────────────────────────────────────

    def _read_input(self) -> Any:
        """Read input — from queue or interactively."""
        if self.input_queue:
            raw = self.input_queue.pop(0)
        elif self.input_callback:
            raw = self.input_callback()
        else:
            raw = input(">>> ")

        raw = str(raw).strip()

        if raw.lower() == 'true':
            return True
        if raw.lower() == 'false':
            return False

        # Try to parse as number
        try:
            if '.' in raw:
                return float(raw)
            return int(raw)
        except ValueError:
            return raw

    # ──────────────────────────── TRACING ──────────────────────────────────────

    def _log_trace(self, instr: BytecodeInstruction):
        """Log a trace entry for step-by-step visualization."""
        frame_name = self.call_stack[-1].func_name if self.call_stack else "global"
        stack_repr = str(self.stack[-5:]) if self.stack else "[]"
        entry = f"[{self.ip:04d}] {frame_name:>10} | {str(instr):<25} | stack: {stack_repr}"
        self.trace_log.append(entry)
