import enum
from typing import List, Iterable

from pysh.syntaxnodes import SyntaxNode, ExpressionNode, ArgumentPartNode, ArgumentNode, ArgumentPartType, \
    SyntaxNodeVisitor


class OpCode(enum.Enum):
    NoOp = 0
    Concat = 1
    Substitute = 2
    SubstituteSingle = 3
    LoadBuffer = 4
    PushBuffer = 5
    ResetA = 6
    IncrementA = 7
    PushA = 8
    Call = 9
    BranchReturnValue = 10
    BranchBufferEmpty = 11
    JumpRelative = 12
    DefineFunction = 13


class Instruction(object):
    @property
    def opcode(self) -> OpCode:
        return OpCode.NoOp

    def accept(self, visitor: 'InstructionVisitor') -> None:
        pass


class ConcatInstruction(Instruction):
    def __init__(self, value: str) -> None:
        self.value = value

    @property
    def opcode(self) -> OpCode:
        return OpCode.Concat

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_concat(self)


class SubstituteInstruction(Instruction):
    def __init__(self, value: str) -> None:
        self.value = value

    @property
    def opcode(self) -> OpCode:
        return OpCode.Substitute

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_substitute(self)


class SubstituteSingleInstruction(Instruction):
    def __init__(self, value: str) -> None:
        self.value = value

    @property
    def opcode(self) -> OpCode:
        return OpCode.SubstituteSingle

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_substitute_single(self)


class LoadBufferInstruction(Instruction):
    def __init__(self, value: str) -> None:
        self.value = value

    @property
    def opcode(self) -> OpCode:
        return OpCode.LoadBuffer

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_load_buffer(self)


class PushBufferInstruction(Instruction):
    def opcode(self) -> OpCode:
        return OpCode.PushBuffer

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_push_buffer(self)


class ResetAInstruction(Instruction):
    def opcode(self) -> OpCode:
        return OpCode.PushBuffer

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_reset_a(self)


class IncrementAInstruction(Instruction):
    def opcode(self) -> OpCode:
        return OpCode.IncrementA

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_increment_a(self)


class PushAInstruction(Instruction):
    def opcode(self) -> OpCode:
        return OpCode.PushA

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_push_a(self)


class CallInstruction(Instruction):
    @property
    def opcode(self) -> OpCode:
        return OpCode.Call

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_call(self)


class BranchReturnValueInstruction(Instruction):
    def __init__(self, offset: int) -> None:
        self.offset = offset

    @property
    def opcode(self) -> OpCode:
        return OpCode.BranchReturnValue

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_branch_return_value(self)


class BranchBufferEmptyInstruction(Instruction):
    def __init__(self, offset: int) -> None:
        self.offset = offset

    @property
    def opcode(self) -> OpCode:
        return OpCode.BranchBufferEmpty

    def accept(self, visitor: 'InstructionVisitor') -> None:
        visitor.visit_branch_buffer_empty(self)


class JumpRelativeInstruction(Instruction):
    def __init__(self, offset: int) -> None:
        self.offset = offset

    @property
    def opcode(self) -> OpCode:
        return OpCode.JumpRelative

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

    def visit_branch_return_value(self, instruction: BranchReturnValueInstruction) -> None:
        pass

    def visit_branch_buffer_empty(self, instruction: BranchBufferEmptyInstruction) -> None:
        pass

    def visit_jump_relative(self, instruction: JumpRelativeInstruction) -> None:
        pass


class CodeGenVisitor(SyntaxNodeVisitor):
    def __init__(self) -> None:
        self.code: List[Instruction] = []

    def visit_argument_part_node(self, node: ArgumentPartNode) -> None:
        pass

    def visit_argument_node(self, node: ArgumentNode) -> None:
        pass

    def visit_expression_node(self, node: ExpressionNode) -> None:
        self.code.append(LoadBufferInstruction(""))
        self.code.append(ResetAInstruction())
        for arg_node in node.args:
            last_part_was_replacement = False
            for part_node in arg_node.parts:
                last_part_was_replacement = False
                if part_node.type == ArgumentPartType.CONSTANT:
                    self.code.append(ConcatInstruction(part_node.value))
                elif part_node.type == ArgumentPartType.REPLACEMENT:
                    self.code.append(SubstituteInstruction(part_node.value))
                    last_part_was_replacement = True
                elif part_node.type == ArgumentPartType.REPLACEMENT_SINGLE:
                    self.code.append(SubstituteSingleInstruction(part_node.value))
                else:
                    raise Exception("bug")

            if last_part_was_replacement:
                self.code.append(BranchBufferEmptyInstruction(2))
            self.code.append(PushBufferInstruction())
            self.code.append(IncrementAInstruction())

        self.code.append(CallInstruction())


class CodeGenerator(object):
    def __init__(self) -> None:
        pass

    def generate(self, syntax_nodes: Iterable[SyntaxNode]) -> List[Instruction]:
        visitor = CodeGenVisitor()
        for node in syntax_nodes:
            node.accept(visitor)
        return visitor.code
