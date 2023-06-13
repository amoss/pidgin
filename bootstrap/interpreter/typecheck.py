# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import functools

from .box import Box
from .frontend import AST
from .types import Type
from ..parser import Token
from ..util import dump

class TypingFailed(Exception):
    def __init__(self, tree, msg):
        self.tree = tree
        super().__init__(msg)


class TypedEnvironment:
    def __init__(self):
        self.types       = {}
        self.values      = {}
        self.expressions = {}
        self.instructions = {}


    def dump(self):
        print('TypedEnv:')
        for name,namedType in self.types.items():
            if name in self.values:
                withVal = f' = {self.values[name]}'
            else:
                withVal = ''
            print(f'  {name} :: {namedType}{withVal}')


    def wipe(self):
        keys = tuple(self.values.keys())
        for k in keys:
            if not self.types[k].isBuiltin():
                del self.values[k]


    def add(self, name, nameType):
        assert isinstance(name,str), name
        assert isinstance(nameType,Type), nameType
        if not name in self.types:
            self.types[name] = nameType
        else:
            self.types[name] = self.types[name].join(nameType)


    def set(self, name, value):
        assert name in self.types, f'Cannot set value for unknown {name}'
        assert isinstance(value,Box), f'Cannot use {value} as value for {name}'
        assert value.type==self.types[name], f'Type mismatch using {value}:{value.type} for {name}:{self.types[name]}'
        self.values[name] = value


    def lookup(self, name):
        return self.values[name], self.types[name]


    def makeChild(self):
        '''A child environment contains references to all functions declared in this environment, but not any
           references to data values.'''
        result = TypedEnvironment()
        for name,nameType in self.types.items():
            if name[:5]=='type '  or  nameType.isFunction()  or  nameType.isBuiltin()  or  nameType.isEnum():
                result.add(name, nameType)
        return result

    def makeCopy(self):
        '''A copy of th environmen is used as an initial state for a call, contains all types but not any values.'''
        result = TypedEnvironment()
        for name,nameType in self.types.items():
            result.add(name, nameType)
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
        exprType = despatch[type(tree)](tree)
        self.expressions[tree] = exprType
        return exprType


    def fromStatement(self, tree):
        if isinstance(tree, AST.Assignment):
            newType = self.fromExpression(tree.expr)
            self.add(tree.target, newType)
        elif isinstance(tree, AST.Return):
            self.add('%return%', self.fromExpression(tree.expr))
        elif isinstance(tree, AST.Call):
            retType = self.makeCall(tree)
            assert retType.isVoid(), f'Call in statement to non-void function {tree.name}'
        elif isinstance(tree, AST.If):
            self.checkCondition(tree.condition)
            self.fromScope(tree.trueStmts)
            if tree.elseStmts is not None:
                self.fromScope(tree.elseStmts)
        elif isinstance(tree, AST.While):
            self.checkCondition(tree.condition)
            self.fromScope(tree.scope)
        elif isinstance(tree, AST.For):
            exprType = self.fromExpression(tree.expr)
            assert exprType.isSet() or exprType.isOrder(), f'Cannot iterate over {exprType}'
            elemType = exprType.param1
            if tree.ident.span in self.types:
                itType = self.makeFromIdent(tree.ident)
                elemType = itType.join(elemType)
            self.add(tree.ident.span, elemType)
            self.fromScope(tree.scope)
        else:
            raise TypingFailed(tree, f'Unexpected statement during type-check {tree}')


    def fromDeclarations(self, tree):
        if isinstance(tree,Token):
            tree = tree.children
        else:
            assert isinstance(tree,tuple), tree
        for c in tree:
            if isinstance(c, AST.FunctionDecl):
                argsContainer = self.makeRecordDecl(c.arguments)
                inside = self.makeChild()
                for argName, argType in argsContainer.params:
                    inside.add(argName, argType)
                inside.fromScope(c.body)
                if not '%return%' in inside.types:
                    raise TypingFailed(c, f'Function did not return a value')
                combined = self.makeTypeDecl(c.retType).join(inside.types['%return%'])
                self.add(c.name, Type.FUNCTION(argsContainer, self.makeTypeDecl(c.retType), inside))
            elif isinstance(c, AST.TypeSynonym):
                theType = self.makeTypeDecl(c.namedType)
                self.add('type '+c.name, theType)
            elif isinstance(c, Token)  and  c.symbol.isNonterminal  and  c.symbol.name=='enum_decl':
                names = list(cc.span for cc in c.children[3:-1])
                enumName = c.children[1].span
                enumType = Type.ENUM(enumName, names)
                self.add('enum '+enumName, enumType)
                for n in names:
                    self.add(n, enumType)
            else:
                raise TypingFailed(c, f'Unable to typecheck {c} at toplevel')

    def fromScope(self, tree):
        assert isinstance(tree,tuple)  or  isinstance(tree,Token)
        if isinstance(tree,Token):
            tree = tree.children
        for c in tree:
            if isinstance(c, AST.FunctionDecl):
                argsContainer = self.makeRecordDecl(c.arguments)
                inside = self.makeChild()
                for argName, argType in argsContainer.params:
                    inside.add(argName, argType)
                inside.fromScope(c.body)
                if not '%return%' in inside.types:
                    raise TypingFailed(c, f'Function did not return a value')
                combined = self.makeTypeDecl(c.retType).join(inside.types['%return%'])
                self.add(c.name, Type.FUNCTION(argsContainer, self.makeTypeDecl(c.retType), inside))
            elif isinstance(c, AST.TypeSynonym):
                theType = self.makeTypeDecl(c.namedType)
                self.add('type '+c.name, theType)
            elif isinstance(c, Token)  and  c.symbol.isNonterminal  and  c.symbol.name=='statement':
                self.fromStatement(c)
            elif type(c) in (AST.Assignment, AST.Return, AST.Call, AST.If, AST.For, AST.While):
                self.fromStatement(c)
            elif isinstance(c, AST.EnumDecl):
                enumType = Type.ENUM(c.name, c.enumNames)
                self.add('enum '+c.name, enumType)
                for n in c.enumNames:
                    self.add(n, enumType)
            else:
                raise TypingFailed(c, f'Unable to typecheck {c}')


    def makeCall(self, tree):
        argType = self.fromExpression(tree.arg)
        if not tree.function in self.types:
            raise TypingFailed(tree, f"Call to unknown function {tree.function}")
        fType = self.types[tree.function]
        checkArg = fType.param1.join(argType)
        return fType.param2


    def makeFromIdent(self, tree):
        if tree.span in ('true','false'):
            return Type.BOOL()
        if not tree.span in self.types:
            self.dump()
            raise TypingFailed(tree, f"Cannot infer type of {tree.span}")
        return self.types[tree.span]


    def makeMap(self, tree):
        raise TypingFailed(tree, "Not implemented yet")


    def makeNumber(self, tree):
        return Type.NUMBER()


    def makeOrder(self, tree):
        if len(tree.seq)==0:         return Type.ORDER(None)
        try:
            return Type.ORDER(functools.reduce(Type.join, [self.fromExpression(e) for e in tree.seq]))
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
            if not typeName in self.types:
                raise TypingFailed(tree, f'Unknown {typeName}')
            return self.types[typeName]
        if tree.terminalAt(0,'type'):
            typeName = f'type {tree.children[1].span}'
            if not typeName in self.types:
                raise TypingFailed(tree, f'Unknown {typeName}')
            return self.types[typeName]
        raise TypingFailed(tree, f'Unexpected type_decl {tree}')

    def makeFromTree(self, tree):
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


    def checkCondition(self, tree):
        despatch = {
            '<': self.checkLess,
            '>': self.checkGreat,
            '==': self.checkEqual,
            '!=': self.checkInequal,
        }
        op = tree.children[1].span
        assert op in despatch, f'Unknown conditional operation {op}'
        lhs = self.fromExpression(tree.children[0])
        rhs = self.fromExpression(tree.children[2])
        despatch[op](lhs,rhs)

    def checkLess(self, lhs, rhs):
        assert lhs==rhs, f'Cannot compare {lhs} and {rhs}'
        if not lhs.isNumber():
            assert False, f'Cannot perform < comparison on {lhs}'
    def checkGreat(self, lhs, rhs):
        assert lhs==rhs, f'Cannot compare {lhs} and {rhs}'
        if not lhs.isNumber():
            assert False, f'Cannot perform > comparison on {lhs}'
    def checkEqual(self, lhs, rhs):
        assert lhs==rhs, f'Cannot compare {lhs} and {rhs}'
        if not lhs.isNumber() and not lhs.isString():
            assert False, f'Cannot perform == comparison on {lhs}'
    def checkInequal(self, lhs, rhs):
        assert lhs==rhs, f'Cannot compare {lhs} and {rhs}'
        if not lhs.isNumber() and not lhs.isString():
            assert False, f'Cannot perform == comparison on {lhs}'

    def checkPlus(self, tree, leftType, rightType):
        if leftType.kind in ('map', 'record'):
            raise TypingFailed(tree ,f'Plus is not defined on {leftType}')
        combined = leftType.join(rightType)
        return combined


