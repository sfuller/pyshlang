from typing import List, Iterable

from pysh.instructions import Instruction, LoadBufferInstruction, ResetAInstruction, ConcatInstruction, \
    SubstituteInstruction, SubstituteSingleInstruction, BranchBufferEmptyInstruction, PushBufferInstruction, \
    IncrementAInstruction, CallInstruction, SetVarInstruction
from pysh.syntaxnodes import SyntaxNode, CommandNode, ArgumentPartNode, ArgumentNode, ArgumentPartType, \
    SyntaxNodeVisitor, AssignmentNode


class CodeGenVisitor(SyntaxNodeVisitor):
    def __init__(self) -> None:
        self.code: List[Instruction] = []

    def visit_argument_part_node(self, node: ArgumentPartNode) -> None:
        pass

    def visit_argument_node(self, node: ArgumentNode) -> None:
        pass

    def visit_command_node(self, node: CommandNode) -> None:
        self.code.append(ResetAInstruction())
        for arg_node in node.args:
            self.code.append(LoadBufferInstruction(""))
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

    def visit_assignment_node(self, node: AssignmentNode) -> None:
        self.code.append(LoadBufferInstruction(node.var_name))
        self.code.append(PushBufferInstruction())
        self.code.append(LoadBufferInstruction(''))
        for part in node.expr.parts:
            if part.type == ArgumentPartType.CONSTANT:
                self.code.append(ConcatInstruction(part.value))
            elif part.type == ArgumentPartType.REPLACEMENT or part.type == ArgumentPartType.REPLACEMENT_SINGLE:
                self.code.append(SubstituteSingleInstruction(part.value))
        self.code.append(SetVarInstruction())


class CodeGenerator(object):
    def __init__(self) -> None:
        pass

    def generate(self, syntax_nodes: Iterable[SyntaxNode]) -> List[Instruction]:
        visitor = CodeGenVisitor()
        for node in syntax_nodes:
            node.accept(visitor)
        return visitor.code
