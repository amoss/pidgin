# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .block import Block, Instruction
from .box import Box
from .frontend import AST
from .types import Type
from ..parser import Token

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


    def assignment(self, stmt):
        print(f'Building assign')
        self.current.defs[stmt.target] = self.expression(stmt.expr)


    def expression(self, expr):
        if isinstance(expr, AST.NumberLit):
            inst = Instruction.CONSTANT( Box(Type.NUMBER(), expr.content) )
            self.current.instructions.append(inst)
            return inst

        if isinstance(expr, AST.StringLit):
            inst = Instruction.CONSTANT( Box(Type.STRING(), expr.content) )
            self.current.instructions.append(inst)
            return inst

        if isinstance(expr, AST.Ident):
            if expr.span in self.current.defs:
                return self.current.defs[expr.span]
            if not expr.span in self.current.uses:
                self.current.uses[expr.span] = Instruction.INPUT(expr.span)
            return self.current.uses[expr.span]


        if isinstance(expr,Token)  and  expr.symbol.isNonterminal  and  expr.tag in ('binop1','binop2'):
            lhs = addExpression(expr.children[0])
            for opChild in expr.children[1:]:
                op = opChild[0].span
                rhs = addExpression(opChild[1])
                cons = despatch[(lhs.typeOf(), rhs.typeOf(), op)]
                inst = cons(lhs,rhs)
                self.current.instructions.append(inst)
                lhs = inst
            return inst

        if isinstance(expr, AST.Call):
            inst = Instruction.CALL( expr.function, self.expression(expr.arg) )
            self.current.instructions.append(inst)
            return inst

        if isinstance(expr, AST.Record):
            return self.record(expr)

        if isinstance(expr, AST.Set):
            return self.set(expr)

        assert False, f'Cannot translate unexpected expression node {expr}'

    def record(self, rec):
        r = Instruction.NEW(self.types.expressions[rec])
        self.current.instructions.append(r)
        for name, valueAST in rec.record.items():
            print(valueAST)
            r = Instruction.RECORD_SET(r, name, self.expression(valueAST))
            self.current.instructions.append(r)
        return r

    def set(self, theSet):
        s = Instruction.NEW(self.types.expressions[theSet])
        self.current.instructions.append(s)
        for valueAST in theSet.elements:
            s = Instruction.SET_INSERT(s, self.expression(valueAST))
            self.current.instructions.append(s)
        return s



class ProgramBuilder:
    class Function:
        def __init__(self, entry, typeEnv):
            self.children = {}
            self.typeEnv = typeEnv
            self.entry = entry

        def dump(self):
            print(f'Function:')
            self.entry.dump()
            for c in self.children.values():
                c.dump()

    def __init__(self, toplevel, typeEnv):
        self.typeEnv = typeEnv
        self.outermost = self.doScope(toplevel, typeEnv)

    def doScope(self, scope, scopeTypes):
        builder = BlockBuilder(scopeTypes)
        builder.fromScope(scope)
        result = ProgramBuilder.Function(builder.entry, scopeTypes)
        if not isinstance(scope, tuple):
            scope = scope.children
        for decl in scope:
            if isinstance(decl, AST.FunctionDecl):
                result.children[decl.name] = self.doScope(decl.body, scopeTypes.names[decl.name].innerEnv)
        return result


