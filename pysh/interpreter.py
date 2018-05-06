import os
import sys
from typing import List, Iterable, Dict, Callable, Tuple

from pysh import builtins
from pysh.builtins import InvokeInfo, test
from pysh.instructions import InstructionVisitor, Instruction, ConcatInstruction, SubstituteInstruction, \
    SubstituteSingleInstruction, LoadBufferInstruction, PushBufferInstruction, ResetAInstruction, \
    IncrementAInstruction, PushAInstruction, CallInstruction, BranchReturnValueInstruction, \
    BranchBufferEmptyInstruction, JumpRelativeInstruction, SetVarInstruction


class Context(object):
    def __init__(self) -> None:
        self.variables: Dict[str, str] = {}
        self.exported_variables: List[str] = []
        self.pwd = os.getcwd()


class ExecutionError(Exception):
    pass


class Interpreter(InstructionVisitor):
    def __init__(self) -> None:
        self.context = Context()
        self.stack: List[str] = []
        self.code: List[Instruction] = []
        self.builtins: Dict[str, Callable[[InvokeInfo], int]] = {}
        self.pc = 0
        self.buffer = ''
        self.reg_a = 0
        self.reg_b = 0
        self.rv = 0

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
        value = self.get_var(instruction.value)
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

        if len(args) is 0:
            return

        command_name = args[0]

        target: Callable[[InvokeInfo], int]
        target = self.builtins.get(command_name)

        if target is None:
            self.rv = 127
            sys.stderr.write('pysh: {0}: command not found\n'.format(command_name))
            return

        invoke_info = InvokeInfo(args[1:], self.get_child_env(), '', self.context.pwd)
        self.rv = target(invoke_info)

    def visit_set_var(self, instruction: SetVarInstruction) -> None:
        var_name = self.stack.pop()
        self.context.variables[var_name] = self.buffer

    def visit_branch_return_value(self, instruction: BranchReturnValueInstruction) -> None:
        raise NotImplementedError()

    def visit_branch_buffer_empty(self, instruction: BranchBufferEmptyInstruction) -> None:
        if len(self.buffer) is 0:
            self.pc += instruction.offset

    def visit_jump_relative(self, instruction: JumpRelativeInstruction) -> None:
        self.pc += instruction.offset

    def get_child_env(self) -> List[Tuple[str, str]]:
        env: List[Tuple[str, str]] = []
        for var_name in self.context.exported_variables:
            env.append((var_name, self.context.variables.get(var_name, '')))
        return env

    def get_var(self, name: str) -> str:
        if name == '?':
            return str(self.rv)
        return self.context.variables.get(name, '')


def install_builtins(interpreter: Interpreter) -> None:
    registry = interpreter.builtins
    registry['ls'] = builtins.ls
    registry['exit'] = builtins.exit
    registry['test'] = builtins.test.test
    registry['echo'] = builtins.echo
    registry['true'] = builtins.true
    registry['false'] = builtins.false
