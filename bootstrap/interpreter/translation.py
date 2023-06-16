# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .box import Box
from .builtins import builtin_len, builtin_print
from .frontend import AST
from .irep import Block, Instruction, Function, Value
from .reachingdefs import calcReachingDefs
from .types import Type
from .typecheck import TypedEnvironment
from ..parser import Token
from ..util import dump

class BlockBuilder:
    def __init__(self, types):
        self.current = Block()
        self.entry   = self.current
        self.types   = types
        self.definitions = {}


    def fromScope(self, scope):
        if not isinstance(scope, tuple):
            scope = scope.children
        for stmt in scope:
            print(f'Building {stmt}')
            if isinstance(stmt, AST.Assignment):
                self.assignment(stmt)
            elif isinstance(stmt, AST.Return):
                self.returnstmt(stmt)
            elif isinstance(stmt, AST.Call):
                inst = Instruction.CALL( stmt.function, self.expression(stmt.arg) )
                self.addInstruction(inst, self.types.types[stmt.function].param2)
            elif type(stmt) in (AST.FunctionDecl, AST.EnumDecl, AST.TypeSynonym):
                pass
            elif isinstance(stmt, AST.If):
                inst = self.condition(stmt.condition)
                header = self.current
                trueBB = Block()
                self.current.connect(True,trueBB)
                self.current = trueBB
                self.fromScope(stmt.trueStmts)        # self.currents updates to merged exit
                mergeBB = Block()
                self.current.connect(True,mergeBB)
                if stmt.elseStmts is not None:
                    falseBB = Block()
                    header.connect(False,falseBB)
                    self.current = falseBB
                    self.fromScope(stmt.elseStmts)   # self.currents updates to merged exit
                    self.current.connect(True,mergeBB)
                else:
                    header.connect(False,mergeBB)
                self.current = mergeBB
            elif isinstance(stmt, AST.While):
                headerBB = Block()
                self.current.connect(True,headerBB)
                self.current = headerBB
                inst = self.condition(stmt.condition)
                bodyBB = Block()
                headerBB.connect(True,bodyBB)
                self.current = bodyBB
                self.fromScope(stmt.scope)        # self.currents updates to merged exit
                self.current.connect(True,headerBB)
                mergeBB = Block()
                headerBB.connect(False,mergeBB)
                self.current = mergeBB
            elif isinstance(stmt, AST.For):
                initBB = Block()
                self.current.connect(True,initBB)
                val = self.expression(stmt.expr)
                iterator = Instruction.ITER_INIT(val)
                elemType = self.types.types[stmt.ident.span]
                self.addInstruction(iterator, Type.ITERATOR(elemType))

                headerBB = Block()
                self.current.connect(True,headerBB)
                self.current = headerBB
                inst = Instruction.ITER_CHECK(iterator)
                self.addInstruction(inst, Type.BOOL())

                mergeBB = Block()
                self.current.connect(False,mergeBB)
                bodyBB = Block()
                self.current.connect(True,bodyBB)
                self.current = bodyBB
                nextVal = Instruction.ITER_ACCESS(iterator)     # TODO: not pure, requires two outputs
                self.addInstruction(nextVal, elemType)
                inst = Instruction.STORE(nextVal, stmt.ident.span)
                self.addInstruction(inst, elemType)
                self.fromScope(stmt.scope)
                self.current.connect(True,headerBB)

                self.current = mergeBB
            else:
                dump(stmt)
                assert False, f'Unrecognised statement during translation {stmt}'


    def assignment(self, stmt):
        print(f'Building assign')
        inst = self.expression(stmt.expr)
        self.current.defs[stmt.target] = inst
        #self.addInstruction( Instruction.STORE(inst, stmt.target), self.types.expressions[stmt.expr])


    def addInstruction(self, inst, instType):
        inst.label = f'{self.current.label}_{len(self.current.instructions)}'
        self.current.instructions.append(inst)
        self.types.instructions[inst] = instType
        return inst

    def condition(self, condition):
        lhs = self.expression(condition.children[0])
        rhs = self.expression(condition.children[2])
        if condition.children[1].span=='<':
            return self.addInstruction( Instruction.LESS(lhs,rhs), Type.BOOL())
        if condition.children[1].span=='>':
            return self.addInstruction( Instruction.GREAT(lhs,rhs), Type.BOOL())
        if condition.children[1].span=='==':
            return self.addInstruction( Instruction.EQUAL(lhs,rhs), Type.BOOL())
        if condition.children[1].span=='!=':
            return self.addInstruction( Instruction.INEQUAL(lhs,rhs), Type.BOOL())
        assert False, f'Unknown conditional in translation {self.children[1].span}'

    def expression(self, expr):
        if isinstance(expr, AST.NumberLit):
            return Value(constant=Box(Type.NUMBER(), expr.content))

        if isinstance(expr, AST.StringLit):
            return Value(constant=Box(Type.STRING(), expr.content))

        if isinstance(expr, AST.Ident):
            print(f'Building expression/Ident {expr.span}')
            if expr.span=="true":
                return Value(constant=Box(Type.BOOL(), True))
            if expr.span=="false":
                return Value(constant=Box(Type.BOOL(), False))
            exprType = self.types.types[expr.span]
            if exprType.isEnum():
                return Value(constant=Box(exprType, exprType.params.index(expr.span)))
            if expr.span in self.current.defs:
                return self.current.defs[expr.span]
            value = Value(instruction=self.addInstruction(Instruction.PHI(expr.span),exprType))
            #value = Value(phi=expr.span)
            #value = Value(instruction=self.addInstruction(Instruction.LOAD(expr.span),exprType))
            self.current.defs[expr.span] = value
            return value

        if isinstance(expr,Token)  and  expr.symbol.isNonterminal  and  expr.tag in ('binop1','binop2'):
            lhs = self.expression(expr.children[0])
            for opChild in expr.children[1:]:
                op = opChild.children[0].span
                rhs = self.expression(opChild.children[1])
                if self.types.instructions[lhs].isNumber() and self.types.instructions[rhs].isNumber():
                    inst = Instruction.ADD_NUMBER(lhs,rhs)
                    self.addInstruction(inst, Type.NUMBER())
                else:
                    assert False, f'Unknown types for add operation'
                lhs = inst
            return Value(instruction=inst)

        if isinstance(expr, AST.Call):
            inst = Instruction.CALL( expr.function, self.expression(expr.arg) )
            return Value(instruction=self.addInstruction(inst, self.types.types[expr.function].param2))

        if isinstance(expr, AST.Record):
            return self.record(expr)

        if isinstance(expr, AST.Set):
            return self.set(expr)

        if isinstance(expr, AST.Order):
            return self.order(expr)

        assert False, f'Cannot translate unexpected expression node {expr}'

    def order(self, theOrd):
        print(f'New order: {self.types.expressions[theOrd]}')
        s = Instruction.NEW(self.types.expressions[theOrd])
        self.addInstruction(s, self.types.expressions[theOrd])
        for valueAST in theOrd.seq:
            s = Instruction.ORD_APPEND(s, self.expression(valueAST))
            self.addInstruction(s, self.types.expressions[theOrd])
        return s


    def record(self, rec):
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
        self.current.defs['%return%'] = self.expression(stmt.expr)

    def set(self, theSet):
        s = Instruction.NEW(self.types.expressions[theSet])
        self.addInstruction(s, self.types.expressions[theSet])
        for valueAST in theSet.elements:
            s = Instruction.SET_INSERT(s, self.expression(valueAST))
            self.addInstruction(s, self.types.expressions[theSet])
        return s



class ProgramBuilder:

    def __init__(self, toplevel):
        self.typeEnv = TypedEnvironment()
        aggregates = Type.SUM(Type.SET(None), Type.ORDER(None), Type.MAP(None,None), Type.STRING())
        self.typeEnv.add('len', Type.FUNCTION(aggregates, Type.NUMBER(), None, builtin=builtin_len))
        printables = Type.SUM(Type.SET(None), Type.ORDER(None), Type.MAP(None,None), Type.RECORD((),), Type.TUPLE((),),
                              Type.STRING(), Type.NUMBER())
        self.typeEnv.add('print', Type.FUNCTION(printables, Type.VOID(), None, builtin=builtin_print))
        self.typeEnv.fromDeclarations(toplevel)
        self.outermost = self.doScope(toplevel, self.typeEnv)
        calcReachingDefs(self.outermost.children['main'].entry)


    def doScope(self, scope, scopeTypes):
        builder = BlockBuilder(scopeTypes)
        builder.fromScope(scope)
        result = Function(builder.entry, scopeTypes)
        if not isinstance(scope, tuple):
            scope = scope.children
        for decl in scope:
            if isinstance(decl, AST.FunctionDecl):
                result.children[decl.name] = self.doScope(decl.body, scopeTypes.types[decl.name].innerEnv)
                result.children[decl.name].name = decl.name
                scopeTypes.types[decl.name].function = result.children[decl.name]
        return result


