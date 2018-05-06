from typing import List

from pysh.instructions import InstructionVisitor, ConcatInstruction, SubstituteInstruction, \
    SubstituteSingleInstruction, LoadBufferInstruction, PushBufferInstruction, ResetAInstruction, \
    IncrementAInstruction, PushAInstruction, CallInstruction, SetVarInstruction, BranchReturnValueInstruction, \
    BranchBufferEmptyInstruction, JumpRelativeInstruction, AddRVToAInstruction, BranchIfANotZeroInstruction, \
    PopAInstruction


class GenerateILVisitor(InstructionVisitor):
    def __init__(self) -> None:
        self.parts: List[str] = []

    def visit_concat(self, instruction: ConcatInstruction) -> None:
        self.parts.append('concat "{0}"\n'.format(instruction.value))

    def visit_substitute(self, instruction: SubstituteInstruction) -> None:
        self.parts.append('sub "{0}"\n'.format(instruction.value))

    def visit_substitute_single(self, instruction: SubstituteSingleInstruction) -> None:
        self.parts.append('subs "{0}"\n'.format(instruction.value))

    def visit_load_buffer(self, instruction: LoadBufferInstruction) -> None:
        self.parts.append('ldbuf "{0}"\n'.format(instruction.value))

    def visit_push_buffer(self, instruction: PushBufferInstruction) -> None:
        self.parts.append('pushbuf\n')

    def visit_reset_a(self, instruction: ResetAInstruction) -> None:
        self.parts.append('reseta\n')

    def visit_increment_a(self, instruction: IncrementAInstruction) -> None:
        self.parts.append('inca\n')

    def visit_push_a(self, instruction: PushAInstruction) -> None:
        self.parts.append('pusha\n')

    def visit_pop_a(self, instruction: PopAInstruction) -> None:
        self.parts.append('popa\n')

    def visit_call(self, instruction: CallInstruction) -> None:
        self.parts.append('call\n')

    def visit_set_var(self, instruction: SetVarInstruction) -> None:
        self.parts.append('setvar\n')

    def visit_branch_return_value(self, instruction: BranchReturnValueInstruction) -> None:
        self.parts.append('brv {0}\n'.format(instruction.offset))

    def visit_branch_buffer_empty(self, instruction: BranchBufferEmptyInstruction) -> None:
        self.parts.append('bbe {0}\n'.format(instruction.offset))

    def visit_branch_if_a_not_zero(self, instruction: BranchIfANotZeroInstruction) -> None:
        self.parts.append('bra nz, {0}\n'.format(instruction.offset))

    def visit_jump_relative(self, instruction: JumpRelativeInstruction) -> None:
        self.parts.append('jr {0}\n'.format(instruction.offset))

    def visit_add_rv_to_a(self, instruction: AddRVToAInstruction) -> None:
        self.parts.append('add rv\n')

    def make_il(self) -> str:
        return ''.join(self.parts)
