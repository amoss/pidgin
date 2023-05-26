# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .types import Type
from ..parser import Token
from .frontend import AST

class TypingFailed(Exception):
    pass


class TypeEnvironment:
    def __init__(self):
        self.lookup = {}


    def set(self, name, nameType):
        assert isinstance(name,str), name
        assert isinstance(nameType,Type), nameType
        if not name in self.lookup:
            self.lookup[name] = nameType
        else:
            self.lookup[name] = self.lookup[name].join(nameType)


    def fromExpression(self, tree):
        despatch = {
            AST.Call:      self.makeCall,
            AST.Ident:     self.makeFromIdent,
            AST.Map:       self.makeMap,
            AST.NumberLit: self.makeNumber,
            AST.Order:     self.makeOrder,
            AST.Record:    self.makeRecord,
            AST.Set:       self.makeSet,
            AST.StringLit: self.makeString,
            Token:         self.makeFromTree
        }
        assert type(tree) in despatch, f'Unknown node-type in AST {type(tree)} during type-check'
        return despatch[type(tree)](tree)


    def fromStatement(self, tree):
        if len(tree.children)==3  and  tree.terminalAt(1,'='):
            newType = self.fromExpression(tree.children[2])
            self.set(tree.children[0].span, newType)
        else:
            raise TypingFailed(f'Unexpected statement during type-check {tree}')


    def fromScope(self, tree):
        for c in tree.children:
            if isinstance(c, AST.FunctionDecl):
                pass
            elif isinstance(c, Token)  and  c.symbol.isNonterminal  and  c.symbol.name=='statement':
                self.fromStatement(c)
            else:
                raise TypingFailed(f'Unable to typecheck {c}')


    def makeCall(self, tree):
        raise TypingFailed("Not implemented yet")


    def makeFromIdent(self, tree):
        if not tree.span in self.lookup:
            raise TypingFailed("Cannot infer type of {tree.span}")
        return self.lookup[tree.span]


    def makeMap(self, tree):
        raise TypingFailed("Not implemented yet")


    def makeNumber(self, tree):
        return Type.NUMBER()


    def makeOrder(self, tree):
        if len(tree.seq)==0:         return Type.ORDER(None)
        try:
            return Type.ORDER(functool.reduce(Types.join, tree.seq))
        except TypingFailed as e:
            raise TypingFailed('Type mismatch in set elements') from e


    def makeRecord(tree):
        raise TypingFailed("Not implemented yet")


    def makeSet(tree):
        if len(tree.elements)==0:    return Type.SET(None)
        try:
            return Type.SET(functool.reduce(Types.join, tree.elements))
        except TypingFailed as e:
            raise TypingFailed('Type mismatch in set elements') from e


    def makeString(tree):
        return Type.STRING()


    def makeFromTree(tree):
        despatch = {
            '+':  plusTypeCheck,
            '.+': postfixTypeCheck,
            '+.': prefixTypeCheck,
            '-':  subTypeCheck,
            '.-': postdropTypeCheck,
            '-.': predropTypeCheck,
            '*':  starTypeCheck,
            '/':  slashTypeCheck
        }
        if not tree.symbol.isNonterminal:
            raise TypingFailed(f'Cannot type tree rooted in {tree}')

        if tree.tag=='binop1':
            listTag = 'binop1_lst'
        elif tree.tag=='binop2':
            listTag = 'binop2_lst'
        else:
            raise TypingFailed(f'Cannot type tree rooted by {tree.tag}')

        curType = typeFromAST(tree.children[0])
        for c in tree.children[1:]:
            assert isinstance(c,Token)  and  c.symbol.isNonterminal  and  c.tag==listTag,\
                   f'Illegal operation {c} under {tree.tag}'
            assert isinstance(c.children[0], Token)  and  c.children[0].isTerminal,\
                   f'Illegal operator {c.children[0]} under {tree.tag}'
            op = c.children[0].span
            assert op in despatch, f'Cannot typecheck unknown operator {op}'
            curType = despatch[op](curType, typeFromAST(c.children[1]))
        return curType



