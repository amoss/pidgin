# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import functools

from .frontend import AST
from .types import Type
from ..parser import Token
from ..util import dump

class TypingFailed(Exception):
    def __init__(self, tree, msg):
        self.tree = tree
        super().__init__(msg)


class TypeEnvironment:
    def __init__(self):
        self.lookup = {}


    def dump(self):
        for name,namedType in self.lookup.items():
            print(f'{name} :: {namedType}')

    def set(self, name, nameType):
        assert isinstance(name,str), name
        assert isinstance(nameType,Type), nameType
        if not name in self.lookup:
            self.lookup[name] = nameType
        else:
            self.lookup[name] = self.lookup[name].join(nameType)


    def makeChild(self):
        '''A child environment contains references to all functions declared in this environment, but not any
           references to data values.'''
        result = TypeEnvironment()
        for name,nameType in self.lookup.items():
            if name[:5]=='type '  or  nameType.isFunction()  or  nameType.isBuiltin()  or  nameType.isEnum():
                result.set(name, nameType)
        return result


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
        elif len(tree.children)>=2  and  tree.terminalAt(0,'return'):
            self.set('%return%', self.fromExpression(tree.children[1]))
        else:
            raise TypingFailed(tree, f'Unexpected statement during type-check {tree}')


    def fromScope(self, tree):
        print(f'fromScope {tree}')
        dump(tree)
        assert isinstance(tree,tuple)  or  isinstance(tree,Token)
        if isinstance(tree,Token):
            tree = tree.children
        for c in tree:
            if isinstance(c, AST.FunctionDecl):
                print(f'Typecheck function {c.name} {c.retType} {c.arguments} {c.body}')
                dump(c.arguments)
                argType = self.makeRecordDecl(c.arguments)
                self.set(c.name, Type.FUNCTION(argType, self.makeTypeDecl(c.retType)))
                self.dump()
                inside = self.makeChild()
                for argName, argType in argType.params:
                    inside.set(argName, argType)
                inside.fromScope(c.body)
                if not '%return%' in inside.lookup:
                    raise TypingFailed(c, f'Function did not return a value')
                combined = self.makeTypeDecl(c.retType).join(inside.lookup['%return%'])
            elif isinstance(c, AST.TypeSynonym):
                theType = self.makeTypeDecl(c.namedType)
                print(f'Typecheck type synonym {c.name} :: {theType}')
                dump(c.namedType)
                self.set('type '+c.name, theType)
            elif isinstance(c, Token)  and  c.symbol.isNonterminal  and  c.symbol.name=='statement':
                self.fromStatement(c)
            elif isinstance(c, Token)  and  c.symbol.isNonterminal  and  c.symbol.name=='enum_decl':
                names = list(cc.span for cc in c.children[3:-1])
                enumName = c.children[1].span
                enumType = Type.ENUM(enumName, names)
                print(f'Typecheck enum {enumName} {enumType}')
                self.set('enum '+enumName, enumType)
                for n in names:
                    self.set(n, enumType)
                self.dump()
            else:
                raise TypingFailed(c, f'Unable to typecheck {c}')


    def makeCall(self, tree):
        dump(tree)
        argType = self.fromExpression(tree.arg)
        print(f"Args are {argType}")
        if not tree.function in self.lookup:
            raise TypingFailed(tree, f"Call to unknown function {tree.function}")
        fType = self.lookup[tree.function]
        checkArg = fType.param1.join(argType)
        checkRet = Type.NUMBER()                        # TODO: return types
        return checkRet


    def makeFromIdent(self, tree):
        if tree.span in ('true','false'):
            return Type.BOOL()
        if not tree.span in self.lookup:
            self.dump()
            raise TypingFailed(tree, f"Cannot infer type of {tree.span}")
        return self.lookup[tree.span]


    def makeMap(self, tree):
        raise TypingFailed(tree, "Not implemented yet")


    def makeNumber(self, tree):
        return Type.NUMBER()


    def makeOrder(self, tree):
        if len(tree.seq)==0:         return Type.ORDER(None)
        try:
            return Type.ORDER(functool.reduce(Types.join, tree.seq))
        except TypingFailed as e:
            raise TypingFailed(e.tree, 'Type mismatch in set elements') from e


    def makeRecord(self, tree):
        keys = set(iv.key for iv in tree.children)
        if len(keys)==1 and None in keys:
            return Type.TUPLE(tuple(self.fromExpression(iv.value) for iv in tree.children))
        if None not in keys:
            return Type.RECORD(tuple((iv.key,self.fromExpression(iv.value)) for iv in tree.children))
        raise TypingFailed(tree, "Cannot mix anonymous- and named-elements in record")


    def makeRecordDecl(self, tree):
        return Type.RECORD(tuple( (c.name, self.makeTypeDecl(c.nameType)) for c in tree.children ))


    def makeSet(self, tree):
        if len(tree.elements)==0:    return Type.SET(None)
        try:
            return Type.SET(functools.reduce(Type.join, tuple(self.fromExpression(e) for e in tree.elements)))
        except TypingFailed as e:
            raise TypingFailed(e.tree, 'Type mismatch in set elements') from e


    def makeString(self, tree):
        return Type.STRING()


    def makeTypeDecl(self, tree):
        if tree.symbol.isTerminal:
            if tree.span=='int':
                return Type.NUMBER()
            if tree.span=='string':
                return Type.STRING()
            if tree.span=='bool':
                return Type.BOOL()
            raise TypingFailed(tree, f'Unexpected type_decl {tree}')
        if tree.terminalAt(0,'set<'):
            return Type.SET(self.makeTypeDecl(tree.children[1]))
        if tree.terminalAt(0,'map<'):
            return Type.MAP(self.makeTypeDecl(tree.children[1]))
        if tree.terminalAt(0,'order<'):
            return Type.ORDER(self.makeTypeDecl(tree.children[1]))
        if tree.terminalAt(0,'['):
            return Type.TUPLE(tuple(self.makeTypeDecl(t) for t in tree.children[1:-1]))
        if tree.terminalAt(0,'enum'):
            typeName = f'enum {tree.children[1].span}'
            if not typeName in self.lookup:
                raise TypingFailed(tree, f'Unknown {typeName}')
            return self.lookup[typeName]
        if tree.terminalAt(0,'type'):
            typeName = f'type {tree.children[1].span}'
            if not typeName in self.lookup:
                raise TypingFailed(tree, f'Unknown {typeName}')
            return self.lookup[typeName]
        raise TypingFailed(tree, f'Unexpected type_decl {tree}')

    def makeFromTree(self, tree):
        print(f'Typecheck {tree}')
        dump(tree)
        despatch = {
            '+':  self.checkPlus,
            #'.+': postfixTypeCheck,
            #'+.': prefixTypeCheck,
            #'-':  subTypeCheck,
            #'.-': postdropTypeCheck,
            #'-.': predropTypeCheck,
            #'*':  starTypeCheck,
            #'/':  slashTypeCheck
        }
        if not tree.symbol.isNonterminal:
            raise TypingFailed(tree, f'Cannot type tree rooted in {tree}')

        if tree.tag=='binop1':
            listTag = 'binop1_lst'
        elif tree.tag=='binop2':
            listTag = 'binop2_lst'
        else:
            raise TypingFailed(tree, f'Cannot type tree rooted by {tree.tag}')

        curType = self.fromExpression(tree.children[0])
        for c in tree.children[1:]:
            assert isinstance(c,Token)  and  c.symbol.isNonterminal  and  c.tag==listTag,\
                   f'Illegal operation {c} under {tree.tag}'
            assert isinstance(c.children[0], Token)  and  c.children[0].symbol.isTerminal,\
                   f'Illegal operator {c.children[0]} under {tree.tag}'
            op = c.children[0].span
            assert op in despatch, f'Cannot typecheck unknown operator {op}'
            curType = despatch[op](c, curType, self.fromExpression(c.children[1]))
        return curType

    def checkPlus(self, tree, leftType, rightType):
        if leftType.kind in ('map', 'record'):
            raise TypingFailed(tree ,f'Plus is not defined on {leftType}')
        combined = leftType.join(rightType)
        return combined


