import sys
from typing import List, Iterable, Dict

from pysh.instructions import InstructionVisitor, Instruction, ConcatInstruction, SubstituteInstruction, \
    SubstituteSingleInstruction, LoadBufferInstruction, PushBufferInstruction, ResetAInstruction, \
    IncrementAInstruction, PushAInstruction, CallInstruction, BranchReturnValueInstruction, \
    BranchBufferEmptyInstruction, JumpRelativeInstruction, SetVarInstruction


class Context(object):
    def __init__(self) -> None:
        self.variables: Dict[str, str] = {}


class ExecutionError(Exception):
    pass


class Interpreter(InstructionVisitor):
    def __init__(self) -> None:
        self.context = Context()
        self.stack: List[str] = []
        self.code: List[Instruction] = []
        self.pc = 0
        self.buffer = ''
        self.reg_a = 0
        self.reg_b = 0

    def execute(self, code: Iterable[Instruction]) -> None:
        self.code.extend(code)
        code_len = len(self.code)
        try:
            while self.pc < code_len:
                instruction = self.code[self.pc]
                instruction.accept(self)
                self.pc += 1
        except ExecutionError as e:
            sys.stderr.write(str(e))

    def visit_concat(self, instruction: ConcatInstruction) -> None:
        self.buffer += instruction.value

    def visit_substitute(self, instruction: SubstituteInstruction) -> None:
        value = self.context.variables.get(instruction.value, '')
        parts = value.split(' ')

        # remove empty parts
        args = [part for part in parts if len(part) > 0]
        arglen = len(args)

        for i in range(arglen - 1):
            self.buffer += args[i]
            self.stack.append(self.buffer)
            self.buffer = ''

        if arglen > 0:
            self.buffer += args[arglen - 1]
            self.reg_a += arglen - 1

    def visit_substitute_single(self, instruction: SubstituteSingleInstruction) -> None:
        self.buffer += self.context.variables.get(instruction.value, '')

    def visit_load_buffer(self, instruction: LoadBufferInstruction) -> None:
        self.buffer = instruction.value

    def visit_push_buffer(self, instruction: PushBufferInstruction) -> None:
        self.stack.append(self.buffer)

    def visit_reset_a(self, instruction: ResetAInstruction) -> None:
        self.reg_a = 0

    def visit_increment_a(self, instruction: IncrementAInstruction) -> None:
        self.reg_a += 1

    def visit_push_a(self, instruction: PushAInstruction) -> None:
        self.stack.append(str(self.reg_a))

    def visit_call(self, instruction: CallInstruction) -> None:
        stack_len = len(self.stack)
        if stack_len < self.reg_a:
            raise ExecutionError('Stack underflow! Bad code given to interpreter or interpreter bug.')
        stack_start = stack_len - self.reg_a
        args = self.stack[stack_start:]
        del self.stack[stack_start:]
        print('CALL ' + repr(args))

    def visit_set_var(self, instruction: SetVarInstruction) -> None:
        var_name = self.stack.pop()
        self.context.variables[var_name] = self.buffer

    def visit_branch_return_value(self, instruction: BranchReturnValueInstruction) -> None:
        raise Exception("TODO")

    def visit_branch_buffer_empty(self, instruction: BranchBufferEmptyInstruction) -> None:
        if len(self.buffer) is 0:
            self.pc += instruction.offset

    def visit_jump_relative(self, instruction: JumpRelativeInstruction) -> None:
        self.pc += instruction.offset
