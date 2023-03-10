# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os, sys
rootDir= os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

import argparse
import string
import sys

from bootstrap.grammar import Grammar
from bootstrap.parser import Parser

def stage1():
    '''
    The subset of the pidgin expression grammar that handles expressions with mostly normal and sane bracketing.
    '''
    g = Grammar("expr")
    g.setDiscard(g.Terminal(set(" \t\r\n"), "some"))

    expr = g.addRule("expr", [g.Nonterminal("binop1")])

    binop1 = g.addRule("binop1", [g.Nonterminal("binop2"), g.Nonterminal("binop1_lst","any")])
    binop1_lst = g.addRule("binop1_lst", [g.Terminal(".+"), g.Nonterminal("binop2")])
    binop1_lst.add(                      [g.Terminal("+."), g.Nonterminal("binop2")])
    binop1_lst.add(                      [g.Terminal(".-"), g.Nonterminal("binop2")])
    binop1_lst.add(                      [g.Terminal("-."), g.Nonterminal("binop2")])
    binop1_lst.add(                      [g.Terminal("+"),  g.Nonterminal("binop2")])
    binop1_lst.add(                      [g.Terminal("-"),  g.Nonterminal("binop2")])

    binop2 = g.addRule("binop2", [g.Nonterminal("binop3"), g.Nonterminal("binop2_lst","any")])
    binop2_lst = g.addRule("binop2_lst", [g.Terminal("*"), g.Nonterminal("binop3")])
    binop2_lst.add(                      [g.Terminal("/"), g.Nonterminal("binop3")])

    binop3 = g.addRule("binop3", [g.Nonterminal("binop4"), g.Nonterminal("binop3_lst","any")])
    binop3_lst = g.addRule("binop3_lst", [g.Terminal("@"), g.Nonterminal("binop4")])

    binop4 = g.addRule("binop4", [g.Nonterminal("ident"), g.Terminal("!"), g.Nonterminal("atom")])
    binop4.add(                  [g.Nonterminal("atom")])

    atom = g.addRule("atom", [g.Terminal(set("0123456789"),"some",tag="num")])
    atom.add(                [g.Terminal("true", tag="bool")])
    atom.add(                [g.Terminal("false", tag="bool")])
    atom.add(                [g.Nonterminal("ident")])
    atom.add(                [g.Nonterminal("str_lit")])
    atom.add(                [g.Nonterminal("set")])
    atom.add(                [g.Nonterminal("map")])
    atom.add(                [g.Nonterminal("order")])
    atom.add(                [g.Nonterminal("record")])
    atom.add(                [g.Terminal("("), g.Nonterminal("expr"), g.Terminal(")")])

    aset = g.addRule("set",    [g.Terminal('{'), g.Nonterminal("elem_lst", "optional"), g.Terminal('}')])
    aord = g.addRule("order",  [g.Terminal('['), g.Nonterminal("elem_lst", "optional"), g.Terminal(']')])
    amap = g.addRule("map",    [g.Terminal('{'), g.Nonterminal("elem_kv",  "some"),  g.Terminal('}')])
    amap.add(                  [g.Terminal('{'), g.Terminal(':'), g.Terminal('}')])
    arec = g.addRule("record", [g.Terminal('['), g.Nonterminal("elem_iv", "some"), g.Terminal(']')])

    g.addRule("elem_kv",  [g.Nonterminal("expr"),
                           g.Terminal(":"),
                           g.Nonterminal("expr"),
                           g.Terminal(",", external="optional")])
    g.addRule("elem_iv",  [g.Nonterminal("ident"),
                           g.Terminal(":"),
                           g.Nonterminal("expr"),
                           g.Terminal(",", external="optional")])
    g.addRule("elem_lst", [g.Nonterminal("repeat_elem", "any"), g.Nonterminal("final_elem")])
    g.addRule("repeat_elem", [g.Nonterminal("expr"), g.Glue(), g.Terminal(set(", \r\t\n"))] )
    g.addRule("final_elem", [g.Nonterminal("expr"), g.Glue(), g.Terminal(set(", \r\t\n"), external="optional")] )

    str_lit = g.addRule("str_lit", [g.Terminal("'"), g.Glue(),
                                    g.Terminal(set('"'), "some", inverse=True, external="optional"), g.Glue(),
                                    g.Terminal('"')])
    str_lit.add(                   [g.Terminal("u("), g.Glue(),
                                    g.Terminal(set(')'), "some", inverse=True, external="optional"), g.Glue(),
                                    g.Terminal(')')])

    letters = string.ascii_lowercase + string.ascii_uppercase
    ident = g.addRule("ident", [g.Terminal(set("_"+letters),"just",tag="ident"), g.Glue(),
                                g.Terminal(set("_"+letters+string.digits), "some", external="optional")])
    return g

def stage2(tree):
    result = Grammar(tree.children[0].key.content)
    functors = { 'T':      (lambda a: result.Terminal(a)),
                 'TA':     (lambda a: result.Terminal(a,"some",external="optional")),
                 'TAN':    (lambda a: result.Terminal(a,"some",external="optional",inverse=True)),
                 'TS':     (lambda a: result.Terminal(a,"some")),
                 'TO':     (lambda a: result.Terminal(a,external="optional")),
                 'N':      (lambda a: result.Nonterminal(a)),
                 'NO':     (lambda a: result.Nonterminal(a,"optional")),
                 'NA':     (lambda a: result.Nonterminal(a,"any")),
                 'NS':     (lambda a: result.Nonterminal(a,"some")),
                 'G':      (lambda a: result.Glue())
               }
    functors2 = { 'T':      (lambda a: result.Terminal(a['chars'],tag=a['tag'])),
                  'TS':     (lambda a: result.Terminal(a['chars'],"some", tag=a['tag'])),
                }
    def unbox(v):
        if isinstance(v,StringLit):
            return v.content
        if isinstance(v,Set):
            return set(unbox(c) for c in v.children)
        if isinstance(v,Record):
            return {k:unbox(v) for k,v in v.record.items()}
        assert False, v
    def symbol(call):
        if isinstance(call.arg,StringLit) or isinstance(call.arg,Set):
            return functors[call.function.content](unbox(call.arg))
        if isinstance(call.arg,Record):
            return functors2[call.function.content](unbox(call.arg))
        assert False, call.arg
    for kv in tree.children:
        try:
            rule = result.addRule(kv.key.content, [symbol(s) for s in kv.value.children[0].seq])
            for clause in kv.value.children[1:]:
                rule.add([symbol(s) for s in clause.seq])
        except Exception as e:
            print(f"Stage2 failed to build in {kv.key} / {kv.value}")
            raise
    return result

class Type:
    def __init__(self, label, param1=None, param2=None):
        self.label  = label
        if label=='{}': assert param1 is not None
        if label=='[]': assert param1 is not None
        assert param1 is None or isinstance(param1,Type) or param1=="empty", param1
        self.param1 = param1
        self.param2 = param2

    def __str__(self):
        if self.label=='[]':
            return f"[{self.param1}]"
        if self.label=='{}':
            return "{" + str(self.param1) + "}"
        if self.label=='{:}':
            return "{" + f"{self.param1}:{self.param2}" + "}"
        if self.label=='[:]':
            return "record"
        return self.label

    def __eq__(self, other):
        if not isinstance(other,Type):  return False
        return self.label==other.label and self.param1==other.param1 and self.param2==other.param2

    def __hash__(self):
        return hash((self.label, self.param1, self.param2))

    def eqOrCoerce(self, other):
        if self==other:                                            return True
        if self.label!=other.label:                                return False
        if self.param2 is None:
            assert other.param2 is None,                           f"{self} ? {other}"
            if self.param1=="empty" or other.param1=="empty":      return True
            return self.param1 is not None and self.param1.eqOrCoerce(other.param1)
        else:
            assert other.param2 is not None,                       f"{self} ? {other}"
            if (self.param1=="empty" or other.param1=="empty") and \
               (self.param2=="empty" or other.param2=="empty"):    return True
            return self.param1 is not None and self.param1.eqOrCoerce(other.param1) and \
                   self.param2 is not None and self.param2.eqOrCoerce(other.param2)

    def join(self, other):
        if self==other: return self
        param1, param2 = None, None
        if isinstance(self.param1,Type) and isinstance(other.param1,Type):
            param1 = self.param1.join(other.param1)
        elif self.param1 == "empty" and other.param1 is not None:
            param1 = other.param1
        elif self.param1 is not None and other.param1 == "empty":
            param1 = self.param1
        if isinstance(self.param2,Type) and isinstance(other.param2,Type):
            param1 = self.param1.join(other.param1)
        elif self.param2 == "empty" and other.param2 is not None:
            param2 = other.param2
        elif self.param2 is not None and other.param2 == "empty":
            param2 = self.param2
        return Type(self.label, param1, param2)

class StringLit:
    def __init__(self, content):
        assert isinstance(content,str), content
        self.content = content
    def __str__(self):
        return "'"+self.content+'"'

class NumberLit:
    def __init__(self, content):
        assert isinstance(content,str), content
        self.content = int(content)
    def __str__(self):
        return str(self.content)


class Ident:
    def __init__(self, content):
        assert isinstance(content,str), content
        self.content = content
    def __str__(self):
        return "id("+self.content+')'


class Call:
    def __init__(self, function, arg):
        if isinstance(function, Parser.Terminal):
            self.function = Ident(function.chars)
        else:
            self.function = function
        self.arg = arg
    def __str__(self):
        return f"{self.function}!{self.arg}"


class Order:
    def __init__(self, children):
        self.seq = children
    def __str__(self):
        return "[" + ", ".join([str(c) for c in self.seq]) + "]"
    def type(self):
        if len(self.seq)==0:
            return '[]'
        return f'[{self.seq[0].type()}]'


class Record:
    def __init__(self, children):
        self.children = children
        self.record = {}
        for c in children:
            self.record[c.key] = c.value
    def __str__(self):
        return "[" + ", ".join([str(c) for c in self.children]) + "]"


class Set:
    def __init__(self, children):
        self.children = children
    def __str__(self):
        return "{" + ", ".join([str(c) for c in self.elements]) + "}"


class Map:
    def __init__(self, children):
        self.children = children
    def __str__(self):
        return "{" + ", ".join([str(c) for c in self.children]) + "}"


class KeyVal:
    def __init__(self, key, value):
        self.key = key
        self.value = value
    def __str__(self):
        return f"{self.key}:{self.value}"


class IdentVal:
    def __init__(self, key, value):
        assert isinstance(key,Ident), key
        self.key = key.content
        self.value = value
    def __str__(self):
        return f"{self.key}:{self.value}"





class Box:
    def __init__(self, type, raw):
        self.type = type
        self.raw = raw

    def __eq__(self, other):
        return isinstance(other,Box) and self.type==other.type and self.raw==other.raw

    def __hash__(self):
        return hash((self.type,self.raw))

    def plusTypeCheck(left, right):
        if not left.eqOrCoerce(right): return None
        if left.label=='{}':
            return lambda l,r: Box(l.type.join(r.type),l.raw | r.raw)
        return lambda l,r: Box(l.type.join(r.type),l.raw+r.raw)

    def postfixTypeCheck(left, right):
        if not left.eqOrCoerce(right): return None
        if (left.label=='[]' and right.label=='[]') or \
           (left.label=='S'  and right.label=='S'):
            return lambda l,r: Box(l.type.join(r.type), l.raw+r.raw)

    def prefixTypeCheck(left, right):
        if not left.eqOrCoerce(right): return None
        if (left.label=='[]' and right.label=='[]') or \
           (left.label=='S'  and right.label=='S'):
            return lambda l,r: Box(l.type.join(r.type), r.raw+l.raw)

    def subTypeCheck(left, right):
        if not left.eqOrCoerce(right): return None
        if left.label=='{}':
            return lambda l,r: Box(l.type.join(r.type),l.raw.difference(r.raw))
        if left.label=='N':
            return lambda l,r: Box(l.type.join(r.type),l.raw-r.raw)

    def postdropTypeCheck(left, right):
        if not left.eqOrCoerce(right): return None
        if (left.label=='[]' and right.label=='[]') or \
           (left.label=='S'  and right.label=='S'):
            return lambda l,r: Box(l.type.join(r.type), l.raw[:-len(r.raw)] if l.raw[-len(r.raw):]==r.raw else l.raw)

    def predropTypeCheck(left, right):
        if not left.eqOrCoerce(right): return None
        if (left.label=='[]' and right.label=='[]') or \
           (left.label=='S'  and right.label=='S'):
            return lambda l,r: Box(l.type.join(r.type), l.raw[len(r.raw):] if l.raw[:len(r.raw)]==r.raw else l.raw)

    def starTypeCheck(left, right):
        def splice(lst,delimiter):
            accumulator = lst.raw[0]
            plus = lambda l,r: Box(l.type.join(r.type),l.raw+r.raw)     # Can't refer to plusTypeCheck, fix later
            for l in lst.raw[1:]:
                accumulator = plus(accumulator, delimiter)
                accumulator = plus(accumulator, l)
            return accumulator
        if left.label=='[]' and right.eqOrCoerce(left.param1):
            return splice
        if not left.eqOrCoerce(right): return None
        if left.label=='{}':
            return lambda l,r: Box(l.type.join(r.type), l.raw & r.raw)

    def slashTypeCheck(left, right):
        if left.label=='S' and right.label=='S':
            return lambda whole,delimiter: Box(Type('[]',param1=Type('S')), [Box(Type('S'),s) for s in whole.raw.split(delimiter.raw)])

    opTypeCheck = {
        '+':  plusTypeCheck,
        '.+': postfixTypeCheck,
        '+.': prefixTypeCheck,
        '-':  subTypeCheck,
        '.-': postdropTypeCheck,
        '-.': predropTypeCheck,
        '*':  starTypeCheck,
        '/':  slashTypeCheck
    }

    @staticmethod
    def evaluateBinop(tree, listTag):
        accumulator = Box.fromConstantExpression(tree.children[0])
        for c in tree.children[1:]:
            assert isinstance(c, Parser.Nonterminal) and c.tag==listTag and len(c.children)==2, c
            assert isinstance(c.children[0], Parser.Terminal), c.children[0]
            value = Box.fromConstantExpression(c.children[1])
            op = c.children[0].chars
            eval = Box.opTypeCheck[op](accumulator.type, value.type)
            assert eval is not None, f"Invalid types for operation: {accumulator.type} {op} {value.type}"
            accumulator = eval(accumulator, value)
        return accumulator

    @staticmethod
    def evaluateBinop1(tree):
        return Box.evaluateBinop(tree, "binop1_lst")

    @staticmethod
    def evaluateBinop2(tree):
        return Box.evaluateBinop(tree, "binop2_lst")

    @staticmethod
    def evaluateOrder(tree):
        if len(tree.seq)==0:  return Box(Type('[]',param1='empty'),[])
        result = [ Box.fromConstantExpression(tree.seq[0]) ]
        for subtree in tree.seq[1:]:
            element = Box.fromConstantExpression(subtree)
            assert result[0].type.eqOrCoerce(element.type), f"Can't store element {element.type} inside [{result[0].type}]!"
            result.append(element)
        return Box(Type('[]', param1=result[0].type), result)

    @staticmethod
    def evaluateSet(tree):
        if len(tree.children)==0: return Box(Type('{}',param1='empty'),frozenset())
        element = Box.fromConstantExpression(tree.children[0])
        elementType = element.type
        result = set([element])
        for subtree in tree.children[1:]:
            element = Box.fromConstantExpression(subtree)
            assert elementType.eqOrCoerce(element.type), f"Can't store element {element.type} inside \{{elementType}}!"
            result.add(element)
        return Box(Type('{}', param1=elementType), frozenset(result))


    @staticmethod
    def fromConstantExpression(node):
        if isinstance(node, NumberLit):
            return Box(Type('N'), node.content)
        if isinstance(node, StringLit):
            return Box(Type('S'), node.content)
        if isinstance(node, Order):
            return Box.evaluateOrder(node)
        if isinstance(node, Set):
            return Box.evaluateSet(node)
        assert not isinstance(node, Ident), f"{node} can't be in constant expression"
        despatch = {
            'binop1': Box.evaluateBinop1,
            'binop2': Box.evaluateBinop2
        }
        assert isinstance(node, Parser.Nonterminal), node
        assert node.tag in despatch, node.tag
        return despatch[node.tag](node)

    def unbox(self):
        if self.type.label=='{}':
            raw = frozenset(box.unbox() for box in self.raw)
        elif self.type.label in ('[]','[:]','{:}'):
            raw = [box.unbox() for box in self.raw]
        else:
            raw = self.raw
        return raw



def onlyElemList(node):
    return isinstance(node.children[1],Parser.Nonterminal) and node.children[1].tag=='elem_lst'
ntTransformer = {
    'str_lit' :     (lambda node: StringLit(node.children[1].chars)),
    'ident':        (lambda node: Ident(node.children[0].content+"".join([c.chars for c in node.children[1:]]))),
    'binop4':       (lambda node: Call(node.children[0], node.children[2])),
    'final_elem':   (lambda node: node.children[0]),
    'repeat_elem':  (lambda node: node.children[0]),
    'order':        (lambda node: Order(node.children[1].children) if onlyElemList(node)
                             else Order(node.children[1:-1])),
    'set':          (lambda node: Set(node.children[1].children) if onlyElemList(node)
                             else Set(node.children[1:-1])),
    'map':          (lambda node: Map(node.children[1:-1])),
    'record':       (lambda node: Record(node.children[1:-1])),
    'elem_kv':      (lambda node: KeyVal(node.children[0], node.children[2])),
    'elem_iv':      (lambda node: IdentVal(node.children[0], node.children[2]))
}
tTransformer = {
    'ident':        (lambda node: Ident(node.chars)),
    'num':          (lambda node: NumberLit(node.chars)),
}


def dump(node, depth=0):
    print(f"{'  '*depth}{type(node)}{node}")
    if hasattr(node,'children'):
        for c in node.children:
            dump(c,depth+1)


if __name__=="__main__":
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-i", "--input")
    argParser.add_argument("-f", "--file")
    args = argParser.parse_args()

    if args.input is None and args.file is None:
        print("Must supply input or file")
        sys.exit(-1)

    grammar = open(os.path.join(rootDir, "tests/pidgin_selfhost/grammar.g")).read()
    stage1g = stage1()
    parser = Parser(stage1g, stage1g.discard)
    stage2g = stage2(list(parser.parse(grammar, ntTransformer=ntTransformer, tTransformer=tTransformer))[0])
    parser = Parser(stage2g, stage1g.discard)

    if args.input is not None:
        trees = list(parser.parse(args.input, trace=open('trace.dot','wt'), ntTransformer=ntTransformer, tTransformer=tTransformer))
    if args.file is not None:
        trees = list(parser.parse(open(args.file).read(), trace=open('trace.dot','wt'), ntTransformer=ntTransformer, tTransformer=tTransformer))

    if len(trees)==0:
        print("Parse error")
        sys.exit(-1)
    if len(trees)>1:
        print(f"Warning: input is ambiguous, had {len(tree)} distinct parses")

    result = Box.fromConstantExpression(trees[0])
    pyResult = result.unbox()
    if isinstance(pyResult,str):
        print(repr(pyResult))
    else:
        print(pyResult)
