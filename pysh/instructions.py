

class Instruction(object):
    def accept(self, visitor: 'InstructionVisitor') -> None:
        pass


class ConcatInstruction(Instruction):
    def __init__(self, value: str) -> None:
        self.value = value

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_concat(self)


class SubstituteInstruction(Instruction):
    def __init__(self, value: str) -> None:
        self.value = value

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_substitute(self)


class SubstituteSingleInstruction(Instruction):
    def __init__(self, value: str) -> None:
        self.value = value

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_substitute_single(self)


class LoadBufferInstruction(Instruction):
    def __init__(self, value: str) -> None:
        self.value = value

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_load_buffer(self)


class PushBufferInstruction(Instruction):
    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_push_buffer(self)


class ResetAInstruction(Instruction):
    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_reset_a(self)


class IncrementAInstruction(Instruction):
    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_increment_a(self)


class PushAInstruction(Instruction):
    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_push_a(self)


class CallInstruction(Instruction):
    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_call(self)


class SetVarInstruction(Instruction):
    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_set_var(self)


class BranchReturnValueInstruction(Instruction):
    def __init__(self, offset: int) -> None:
        self.offset = offset

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_branch_return_value(self)


class BranchBufferEmptyInstruction(Instruction):
    def __init__(self, offset: int) -> None:
        self.offset = offset

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_branch_buffer_empty(self)


class JumpRelativeInstruction(Instruction):
    def __init__(self, offset: int) -> None:
        self.offset = offset

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_jump_relative(self)


class InstructionVisitor(object):
    def visit_concat(self, instruction: ConcatInstruction) -> None:
        pass

    def visit_substitute(self, instruction: SubstituteInstruction) -> None:
        pass

    def visit_substitute_single(self, instruction: SubstituteSingleInstruction) -> None:
        pass

    def visit_load_buffer(self, instruction: LoadBufferInstruction) -> None:
        pass

    def visit_push_buffer(self, instruction: PushBufferInstruction) -> None:
        pass

    def visit_reset_a(self, instruction: ResetAInstruction) -> None:
        pass

    def visit_increment_a(self, instruction: IncrementAInstruction) -> None:
        pass

    def visit_push_a(self, instruction: PushAInstruction) -> None:
        pass

    def visit_call(self, instruction: CallInstruction) -> None:
        pass

    def visit_set_var(self, instruction: SetVarInstruction) -> None:
        pass

    def visit_branch_return_value(self, instruction: BranchReturnValueInstruction) -> None:
        pass

    def visit_branch_buffer_empty(self, instruction: BranchBufferEmptyInstruction) -> None:
        pass

    def visit_jump_relative(self, instruction: JumpRelativeInstruction) -> None:
        pass
