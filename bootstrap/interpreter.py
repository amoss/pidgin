# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os, sys
rootDir= os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

import argparse
import sys

from bootstrap.grammar import Grammar
from bootstrap.parser import Parser
import bootstrap.selfhost as selfhost

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
    def symbol(call):
        if isinstance(call.arg,StringLit):
            arg = call.arg.content
        else:
            arg = set(c.content for c in call.arg.children)
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
    def type(self):
        return 'S'


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


def dump(node, depth=0):
    print(f"{'  '*depth}{type(node)}{node}")
    if hasattr(node,'children'):
        for c in node.children:
            dump(c,depth+1)

def evaluateBinop1(tree):
    accumulator = evaluate(tree.children[0])
    for c in tree.children[1:]:
        assert isinstance(c, Parser.Nonterminal) and c.tag=="binop1_lst" and len(c.children)==2, c
        assert isinstance(c.children[0], Parser.Terminal), c.children[0]
        value = evaluate(c.children[1])
        if c.children[0].chars=='+':
            accumulator += value
        else:
            assert False, c.children[0]
    return accumulator

def evaluateOrder(tree):
    t = tree.seq[0].type()
    result = [ evaluate(tree.seq[0]) ]
    for element in tree.seq[1:]:
        assert element.type()==t, f"Can't store {element.type()} in [{t}]!"
        result.append( evaluate(element) )
    return result

def evaluate(tree):
    dump(tree)
    if isinstance(tree, StringLit):
        return tree.content
    if isinstance(tree, Order):
        return evaluateOrder(tree)
    despatch = {
        'binop1': evaluateBinop1
    }
    assert isinstance(tree, Parser.Nonterminal), tree
    assert tree.tag in despatch, tree.tag
    return despatch[tree.tag](tree)


if __name__=="__main__":
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-i", "--input")
    argParser.add_argument("-f", "--file")
    args = argParser.parse_args()

    if args.input is None and args.file is None:
        print("Must supply input or file")
        sys.exit(-1)

    grammar = open(os.path.join(rootDir, "tests/pidgin_selfhost/grammar.g")).read()
    stage1g = selfhost.stage1()
    parser = Parser(stage1g, stage1g.discard)
    stage2g = stage2(list(parser.parse(grammar, transformer=transformer))[0])
    parser = Parser(stage2g, stage1g.discard)

    if args.input is not None:
        trees = list(parser.parse(args.input, trace=open('trace.dot','wt'), transformer=transformer))
    if args.file is not None:
        trees = list(parser.parse(open(args.file).read(), trace=open('trace.dot','wt'), transformer=transformer))

    if len(trees)==0:
        print("Parse error")
        sys.exit(-1)
    if len(trees)>1:
        print(f"Warning: input is ambiguous, had {len(tree)} distinct parses")

    result = evaluate(trees[0])
    print(result)
    
    
