# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os, sys
rootDir= os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

import argparse
import string
import sys

from bootstrap.parser import Parser
from bootstrap.grammar import Grammar

def dump(node, depth=0):
    print(f"{'  '*depth}{type(node)}{node}")
    if hasattr(node,'children'):
        for c in node.children:
            dump(c,depth+1)


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

    atom = g.addRule("atom", [g.Terminal(set("0123456789"),"some")])
    atom.add(                [g.Terminal("true")])
    atom.add(                [g.Terminal("false")])
    atom.add(                [g.Nonterminal("ident")])
    atom.add(                [g.Nonterminal("str_lit")])
    atom.add(                [g.Nonterminal("set")])
    atom.add(                [g.Nonterminal("map")])
    atom.add(                [g.Nonterminal("order")])
    atom.add(                [g.Terminal("("), g.Nonterminal("expr"), g.Terminal(")")])

    aset = g.addRule("set",   [g.Terminal('{'), g.Nonterminal("elem_lst", "optional"), g.Terminal('}')])
    aord = g.addRule("order", [g.Terminal('['), g.Nonterminal("elem_lst", "optional"), g.Terminal(']')])
    amap = g.addRule("map",   [g.Terminal('{'), g.Nonterminal("elem_kv",  "some"),  g.Terminal('}')])
    amap.add(                 [g.Terminal('{'), g.Terminal(':'), g.Terminal('}')])

    g.addRule("elem_kv",  [g.Nonterminal("expr"),
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
    ident = g.addRule("ident", [g.Terminal(set("_"+letters),"just"), g.Glue(),
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
                 'NA':     (lambda a: result.Nonterminal(a,"any")),
                 'NS':     (lambda a: result.Nonterminal(a,"some")),
                 'G':      (lambda a: result.Glue())
               }
    def symbol(call):
        if isinstance(call.arg,StringLit):
            arg = call.arg.content
        else:
            arg = set(c.content for c in call.arg.children)
        print(f"Make symbol from {call.function.content} {arg}")
        assert isinstance(arg,str) or isinstance(arg,set), arg
        return functors[call.function.content](arg)
    for kv in tree.children:
        rule = result.addRule(kv.key.content, [symbol(s) for s in kv.value.children[0].seq])
        for clause in kv.value.children[1:]:
            rule.add([symbol(s) for s in clause.seq])
    return result

class StringLit:
    def __init__(self, content):
        assert isinstance(content,str), content
        self.content = content
    def __str__(self):
        return "'"+self.content+'"'


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


class Set:
    def __init__(self, children):
        self.children = children
    def __str__(self):
        return "{" + ", ".join([str(c) for c in self.children]) + "}"


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


def onlyElemList(node):
    return isinstance(node.children[1],Parser.Nonterminal) and node.children[1].tag=='elem_lst'
transformer = {
    'str_lit' :     (lambda node: StringLit(node.children[1].chars)),
    'ident':        (lambda node: Ident("".join([c.chars for c in node.children]))),
    'binop4':       (lambda node: Call(node.children[0], node.children[2])),
    'final_elem':   (lambda node: node.children[0]),
    'repeat_elem':  (lambda node: node.children[0]),
    'order':        (lambda node: Order(node.children[1].children) if onlyElemList(node)
                             else Order(node.children[1:-1])),
    'set':          (lambda node: Set(node.children[1].children) if onlyElemList(node)
                             else Set(node.children[1:-1])),
    'map':          (lambda node: Map(node.children[1:-1])),
    'elem_kv':      (lambda node: KeyVal(node.children[0], node.children[2]))
}


if __file__=="__main__":
    argParser = argparse.ArgumentParser()
    argParser.add_argument("grammar")
    argParser.add_argument("input")
    args = argParser.parse_args()

    source = open(args.grammar).read()
    input = open(args.input).read()
    g = stage1()
    g.dump()
    parser = Parser(g, g.discard)
    res = list(parser.parse(source, transformer=transformer))
    if len(res)==0:
        print("Failed to parse!")
        sys.exit(-1)
    elif len(res)>1:
        print("Result was ambiguous!")
        sys.exit(-1)

    g2 = stage2(res[0])
    g2.dump()
    parser = Parser(g2, g.discard)
    parser.dotAutomaton(open("lr0.dot","wt"))
    res2 = list(parser.parse(input, trace=open('trace.dot','wt'), transformer=transformer))
    print(res2)
    #dump(res2[0])




