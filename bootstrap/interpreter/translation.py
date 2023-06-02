# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .box import Box
from .builtins import builtin_len
from .frontend import AST
from .irep import Block, Instruction, Function
from .types import Type
from .typecheck import TypedEnvironment
from ..parser import Token
from ..util import dump

class BlockBuilder:
    def __init__(self, types):
        self.current = Block()
        self.entry   = self.current
        self.types   = types


    def fromScope(self, scope):
        if not isinstance(scope, tuple):
            scope = scope.children
        for stmt in scope:
            print(f'Building {stmt}')
            if isinstance(stmt, AST.Assignment):
                self.assignment(stmt)
            elif isinstance(stmt, AST.Return):
                self.returnstmt(stmt)


    def assignment(self, stmt):
        print(f'Building assign')
        self.current.defs[stmt.target] = self.expression(stmt.expr)


    def addInstruction(self, inst, instType):
        self.current.instructions.append(inst)
        self.types.instructions[inst] = instType
        return inst

    def expression(self, expr):
        if isinstance(expr, AST.NumberLit):
            inst = Instruction.CONSTANT( Box(Type.NUMBER(), expr.content) )
            return self.addInstruction(inst, Type.NUMBER())

        if isinstance(expr, AST.StringLit):
            inst = Instruction.CONSTANT( Box(Type.STRING(), expr.content) )
            return self.addInstruction(inst, Type.STRING())

        if isinstance(expr, AST.Ident):
            print(f'Building expression/Ident {expr.span}')
            if expr.span=="true":
                return self.addInstruction( Instruction.CONSTANT( Box(Type.BOOL(), True) ), Type.BOOL() )
            if expr.span=="false":
                return self.addInstruction( Instruction.CONSTANT( Box(Type.BOOL(), False) ), Type.BOOL() )
            if expr.span in self.current.defs:
                return self.current.defs[expr.span]
            inst = Instruction.INPUT(expr.span)
            self.current.defs[expr.span] = inst
            return self.addInstruction(inst, self.types.types[expr.span])


        if isinstance(expr,Token)  and  expr.symbol.isNonterminal  and  expr.tag in ('binop1','binop2'):
            lhs = self.expression(expr.children[0])
            dump(expr)
            for opChild in expr.children[1:]:
                op = opChild.children[0].span
                rhs = self.expression(opChild.children[1])
                if self.types.instructions[lhs].isNumber() and self.types.instructions[rhs].isNumber():
                    inst = Instruction.ADD_NUMBER(lhs,rhs)
                    self.addInstruction(inst, Type.NUMBER())
                else:
                    assert False, f'Unknown types for add operation'
                lhs = inst
            return inst

        if isinstance(expr, AST.Call):
            inst = Instruction.CALL( expr.function, self.expression(expr.arg) )
            return self.addInstruction(inst, self.types.types[expr.function].param2)

        if isinstance(expr, AST.Record):
            return self.record(expr)

        if isinstance(expr, AST.Set):
            return self.set(expr)

        assert False, f'Cannot translate unexpected expression node {expr}'

    def record(self, rec):
        dump(rec)
        recType = self.types.expressions[rec]
        r = Instruction.NEW(recType)
        self.addInstruction(r, recType)
        if recType.isRecord():
            for name, valueAST in rec.record.items():
                r = Instruction.RECORD_SET(r, name, self.expression(valueAST))
                self.addInstruction(r, recType)
            return r
        if recType.isTuple():
            for pos, identVal in enumerate(rec.children):
                r = Instruction.TUPLE_SET(r, pos, self.expression(identVal.value))
                self.addInstruction(r, recType)
            return r
        assert False, f'AST.Record must describe either a named-record or a tuple'

    def returnstmt(self, stmt):
        print(f'Building return')
        self.current.defs['%return%'] = self.expression(stmt.expr)

    def set(self, theSet):
        s = Instruction.NEW(self.types.expressions[theSet])
        self.current.instructions.append(s)
        for valueAST in theSet.elements:
            s = Instruction.SET_INSERT(s, self.expression(valueAST))
            self.addInstruction(s, self.types.expressions[theSet])
        return s



class ProgramBuilder:

    def __init__(self, toplevel):
        self.typeEnv = TypedEnvironment()
        aggregates = Type.SUM(Type.SET(None), Type.ORDER(None), Type.MAP(None,None))
        self.typeEnv.add('len', Type.FUNCTION(aggregates, Type.NUMBER(), None, builtin=builtin_len))
        self.typeEnv.fromScope(toplevel)
        self.outermost = self.doScope(toplevel, self.typeEnv)

    def doScope(self, scope, scopeTypes):
        builder = BlockBuilder(scopeTypes)
        builder.fromScope(scope)
        result = Function(builder.entry, scopeTypes)
        if not isinstance(scope, tuple):
            scope = scope.children
        for decl in scope:
            if isinstance(decl, AST.FunctionDecl):
                result.children[decl.name] = self.doScope(decl.body, scopeTypes.types[decl.name].innerEnv)
                scopeTypes.types[decl.name].function = result.children[decl.name]
        return result


