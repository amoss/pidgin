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

def build():
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
        self.children = children
    def __str__(self):
        return "[" + ", ".join([str(c) for c in self.children]) + "]"

class Set:
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

def transformer(node):
    if isinstance(node, Parser.Nonterminal) and node.tag=='str_lit':
        return StringLit(node.children[1].chars)
    if isinstance(node, Parser.Nonterminal) and node.tag=='ident':
        return Ident("".join([c.chars for c in node.children]))
    if isinstance(node, Parser.Nonterminal) and node.tag=='binop4':
        return Call(node.children[0], node.children[2])
    if isinstance(node, Parser.Nonterminal) and node.tag=='final_elem':
        return node.children[0]
    if isinstance(node, Parser.Nonterminal) and node.tag=='repeat_elem':
        return node.children[0]
    if isinstance(node, Parser.Nonterminal) and node.tag=='order' and\
       isinstance(node.children[1],Parser.Nonterminal) and node.children[1].tag=='elem_lst':
        return Order(node.children[1].children)
    if isinstance(node, Parser.Nonterminal) and node.tag=='order':
        return Order(node.children[1:-1])
    if isinstance(node, Parser.Nonterminal) and node.tag=='set' and\
       isinstance(node.children[1],Parser.Nonterminal) and len(node.children)==3:
        return Set(node.children[1].children)
    if isinstance(node, Parser.Nonterminal) and node.tag=='set':
        return Set(node.children[1:-1])
    if isinstance(node, Parser.Nonterminal) and node.tag=='elem_kv':
        return KeyVal(node.children[0], node.children[2])
    return None

def prune(node):
    if isinstance(node, Parser.Terminal):
        pruned = node
    elif len(node.children)==1:
        pruned = prune(node.children[0])
    else:
        result = [ prune(c) for c in node.children]
        node.children = tuple(result)
        pruned = node

    replacement = transformer(pruned)
    if replacement is not None:
        return replacement
    return pruned

def dump(node, depth=0):
    print(f"{'  '*depth}{type(node)}{node}")
    if hasattr(node,'children'):
        for c in node.children:
            dump(c,depth+1)

argParser = argparse.ArgumentParser()
argParser.add_argument("grammar")
args = argParser.parse_args()

source = open(args.grammar).read()
g = build()
parser = Parser(g, g.discard)
res = list(parser.parse(source))
if len(res)==0:
    print("Failed to parse!")
    sys.exit(-1)
elif len(res)>1:
    print("Result was ambiguous!")
    sys.exit(-1)

dump(prune(res[0]))




