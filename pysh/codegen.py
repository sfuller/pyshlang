from typing import List, Iterable, Optional

from pysh.instructions import Instruction, LoadBufferInstruction, ResetAInstruction, ConcatInstruction, \
    SubstituteInstruction, SubstituteSingleInstruction, BranchBufferEmptyInstruction, PushBufferInstruction, \
    IncrementAInstruction, CallInstruction, SetVarInstruction, PushAInstruction, PopAInstruction, AddRVToAInstruction, \
    BranchReturnValueInstruction, JumpRelativeInstruction, BranchIfANotZeroInstruction
from pysh.syntaxnodes import SyntaxNode, CommandNode, ArgumentPartNode, ArgumentNode, ArgumentPartType, \
    SyntaxNodeVisitor, AssignmentNode, AssignmentsNode, ConditionalNode


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

    def visit_assignments_node(self, node: AssignmentsNode) -> None:
        for assignment_node in node.assignments:
            self.visit_assignment_node(assignment_node)

    def visit_conditional_node(self, node: ConditionalNode) -> None:
        self.code.append(ResetAInstruction())
        for expr in node.evaluation_expressions:
            self.code.append(PushAInstruction())
            expr.accept(self)
            self.code.append(PopAInstruction())
            self.code.append(AddRVToAInstruction())
            self.code.append(PushAInstruction())

        self.code.append(PopAInstruction())
        branch_ins = BranchIfANotZeroInstruction(0)
        start_pos = len(self.code)
        self.code.append(branch_ins)

        for expr in node.conditional_expressions:
            expr.accept(self)

        skip_else_jump_ins: Optional[JumpRelativeInstruction] = None
        skip_else_jump_pos = len(self.code)
        if len(node.else_expressions) > 0:
            skip_else_jump_ins = JumpRelativeInstruction(0)
            self.code.append(skip_else_jump_ins)

        condition_false_pos = len(self.code)

        for expr in node.else_expressions:
            expr.accept(self)

        end_pos = len(self.code)

        branch_ins.offset = condition_false_pos - 1 - start_pos
        if skip_else_jump_ins is not None:
            skip_else_jump_ins.offset = end_pos - 1 - skip_else_jump_pos


class CodeGenerator(object):
    def __init__(self) -> None:
        pass

    def generate(self, syntax_nodes: Iterable[SyntaxNode]) -> List[Instruction]:
        visitor = CodeGenVisitor()
        for node in syntax_nodes:
            node.accept(visitor)
        return visitor.code
