"""
MiniLang Compiler — Stage 4: Intermediate Code Generator
==========================================================
Generates Three-Address Code (TAC) from the annotated AST.
TAC is a linear IR where each instruction has at most 3 operands.
"""

from dataclasses import dataclass
from typing import List, Optional, Any
from .ast_nodes import *
from .errors import IRError


@dataclass
class TACInstruction:
    """A single Three-Address Code instruction."""
    op: str
    result: Optional[str] = None
    arg1: Optional[Any] = None
    arg2: Optional[Any] = None
    label: Optional[str] = None

    def __repr__(self):
        if self.op == 'LABEL':
            return f"{self.label}:"
        elif self.op == 'GOTO':
            return f"  GOTO {self.label}"
        elif self.op == 'IF_FALSE':
            return f"  IF_FALSE {self.arg1} GOTO {self.label}"
        elif self.op == 'CALL':
            return f"  {self.result} = CALL {self.arg1}, {self.arg2}"
        elif self.op == 'PARAM' and self.result:
            return f"  PARAM {self.result} : {self.arg1}"
        elif self.op == 'PARAM':
            return f"  PARAM {self.arg1}"
        elif self.op == 'RETURN':
            return f"  RETURN {self.arg1}" if self.arg1 is not None else "  RETURN"
        elif self.op == 'PRINT':
            return f"  PRINT {self.arg1}"
        elif self.op == 'INPUT':
            return f"  {self.result} = INPUT"
        elif self.op == 'FUNC_BEGIN':
            return f"\nFUNC_BEGIN {self.arg1}"
        elif self.op == 'FUNC_END':
            return f"FUNC_END {self.arg1}"
        elif self.op == 'ASSIGN':
            return f"  {self.result} = {self.arg1}"
        elif self.op == 'ARRAY_STORE':
            return f"  {self.result}[{self.arg1}] = {self.arg2}"
        elif self.op == 'ARRAY_LOAD':
            return f"  {self.result} = {self.arg1}[{self.arg2}]"
        elif self.op == 'ARRAY_ALLOC':
            return f"  {self.result} = ARRAY_ALLOC {self.arg1}"
        elif self.op == 'NEG':
            return f"  {self.result} = NEG {self.arg1}"
        elif self.op == 'NOT':
            return f"  {self.result} = NOT {self.arg1}"
        elif self.arg2 is not None:
            return f"  {self.result} = {self.arg1} {self.op} {self.arg2}"
        else:
            return f"  {self.op} {self.result or ''} {self.arg1 or ''}".strip()


class IRGenerator:
    """Generates Three-Address Code from the AST."""

    def __init__(self):
        self.instructions: List[TACInstruction] = []
        self.temp_counter = 0
        self.label_counter = 0

    def generate(self, program: ProgramNode) -> List[TACInstruction]:
        for func in program.functions:
            self._gen_function(func)
        return self.instructions

    def _new_temp(self) -> str:
        name = f"t{self.temp_counter}"
        self.temp_counter += 1
        return name

    def _new_label(self) -> str:
        name = f"L{self.label_counter}"
        self.label_counter += 1
        return name

    def _emit(self, op, result=None, arg1=None, arg2=None, label=None):
        self.instructions.append(TACInstruction(op, result, arg1, arg2, label))

    def _gen_function(self, func: FunctionNode):
        self._emit('FUNC_BEGIN', arg1=func.name)
        for param in func.params:
            self._emit('PARAM', result=param.name, arg1=param.param_type)
        self._gen_block(func.body)
        if func.return_type == 'void':
            if not self.instructions or self.instructions[-1].op != 'RETURN':
                self._emit('RETURN')
        self._emit('FUNC_END', arg1=func.name)

    def _gen_block(self, block: BlockNode):
        for stmt in block.statements:
            self._gen_statement(stmt)

    def _gen_statement(self, stmt: ASTNode):
        if isinstance(stmt, VarDeclNode):
            self._gen_var_decl(stmt)
        elif isinstance(stmt, AssignNode):
            self._gen_assign(stmt)
        elif isinstance(stmt, IfNode):
            self._gen_if(stmt)
        elif isinstance(stmt, WhileNode):
            self._gen_while(stmt)
        elif isinstance(stmt, ForNode):
            self._gen_for(stmt)
        elif isinstance(stmt, ReturnNode):
            self._gen_return(stmt)
        elif isinstance(stmt, PrintNode):
            self._gen_print(stmt)
        elif isinstance(stmt, ExprStmtNode):
            self._gen_expression(stmt.expression)

    def _gen_var_decl(self, node: VarDeclNode):
        if node.array_size is not None:
            self._emit('ARRAY_ALLOC', result=node.name, arg1=node.array_size)
        elif node.initializer:
            value = self._gen_expression(node.initializer)
            self._emit('ASSIGN', result=node.name, arg1=value)
        else:
            default = 0 if node.var_type in ('int', 'float') else ('false' if node.var_type == 'bool' else '""')
            self._emit('ASSIGN', result=node.name, arg1=default)

    def _gen_assign(self, node: AssignNode):
        value = self._gen_expression(node.value)
        if isinstance(node.target, ArrayAccessNode):
            array_name = self._gen_expression(node.target.array)
            index = self._gen_expression(node.target.index)
            self._emit('ARRAY_STORE', result=array_name, arg1=index, arg2=value)
        elif isinstance(node.target, IdentifierNode):
            self._emit('ASSIGN', result=node.target.name, arg1=value)

    def _gen_if(self, node: IfNode):
        cond = self._gen_expression(node.condition)
        if node.else_block:
            l_else = self._new_label()
            l_end = self._new_label()
            self._emit('IF_FALSE', arg1=cond, label=l_else)
            self._gen_block(node.then_block)
            self._emit('GOTO', label=l_end)
            self._emit('LABEL', label=l_else)
            self._gen_block(node.else_block)
            self._emit('LABEL', label=l_end)
        else:
            l_end = self._new_label()
            self._emit('IF_FALSE', arg1=cond, label=l_end)
            self._gen_block(node.then_block)
            self._emit('LABEL', label=l_end)

    def _gen_while(self, node: WhileNode):
        l_start = self._new_label()
        l_end = self._new_label()
        self._emit('LABEL', label=l_start)
        cond = self._gen_expression(node.condition)
        self._emit('IF_FALSE', arg1=cond, label=l_end)
        self._gen_block(node.body)
        self._emit('GOTO', label=l_start)
        self._emit('LABEL', label=l_end)

    def _gen_for(self, node: ForNode):
        l_start = self._new_label()
        l_end = self._new_label()
        if node.init:
            self._gen_statement(node.init)
        self._emit('LABEL', label=l_start)
        if node.condition:
            cond = self._gen_expression(node.condition)
            self._emit('IF_FALSE', arg1=cond, label=l_end)
        self._gen_block(node.body)
        if node.update:
            self._gen_statement(node.update)
        self._emit('GOTO', label=l_start)
        self._emit('LABEL', label=l_end)

    def _gen_return(self, node: ReturnNode):
        if node.value:
            value = self._gen_expression(node.value)
            self._emit('RETURN', arg1=value)
        else:
            self._emit('RETURN')

    def _gen_print(self, node: PrintNode):
        value = self._gen_expression(node.value)
        self._emit('PRINT', arg1=value)

    def _gen_expression(self, node: ASTNode) -> str:
        if isinstance(node, NumberNode):
            return str(node.value)
        elif isinstance(node, StringNode):
            return f'"{node.value}"'
        elif isinstance(node, BoolNode):
            return str(node.value).lower()
        elif isinstance(node, IdentifierNode):
            return node.name
        elif isinstance(node, BinaryOpNode):
            left = self._gen_expression(node.left)
            right = self._gen_expression(node.right)
            temp = self._new_temp()
            self._emit(node.op, result=temp, arg1=left, arg2=right)
            return temp
        elif isinstance(node, UnaryOpNode):
            operand = self._gen_expression(node.operand)
            temp = self._new_temp()
            self._emit('NEG' if node.op == '-' else 'NOT', result=temp, arg1=operand)
            return temp
        elif isinstance(node, FunctionCallNode):
            arg_temps = []
            for arg in node.arguments:
                arg_temps.append(self._gen_expression(arg))
            for a in arg_temps:
                self._emit('PARAM', arg1=a)
            temp = self._new_temp()
            self._emit('CALL', result=temp, arg1=node.name, arg2=len(node.arguments))
            return temp
        elif isinstance(node, ArrayAccessNode):
            arr = self._gen_expression(node.array)
            idx = self._gen_expression(node.index)
            temp = self._new_temp()
            self._emit('ARRAY_LOAD', result=temp, arg1=arr, arg2=idx)
            return temp
        elif isinstance(node, InputNode):
            temp = self._new_temp()
            self._emit('INPUT', result=temp)
            return temp
        raise IRError(f"Cannot generate IR for: {type(node).__name__}")
