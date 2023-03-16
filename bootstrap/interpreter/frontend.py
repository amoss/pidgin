# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import string

from ..grammar import Grammar
from ..parser import Parser

def stage1():
    '''
    The subset of the pidgin expression grammar that handles expressions with mostly normal and sane bracketing.
    '''
    g = Grammar("expr")
    g.setDiscard(g.TermSet(set(" \t\r\n"), modifier="some"))

    expr = g.addRule("expr", [g.Nonterminal("binop1")])

    binop1 = g.addRule("binop1", [g.Nonterminal("binop2"), g.Nonterminal("binop1_lst",modifier="any")])
    binop1_lst = g.addRule("binop1_lst", [g.TermString(".+"), g.Nonterminal("binop2")])
    binop1_lst.add(                      [g.TermString("+."), g.Nonterminal("binop2")])
    binop1_lst.add(                      [g.TermString(".-"), g.Nonterminal("binop2")])
    binop1_lst.add(                      [g.TermString("-."), g.Nonterminal("binop2")])
    binop1_lst.add(                      [g.TermString("+"),  g.Nonterminal("binop2")])
    binop1_lst.add(                      [g.TermString("-"),  g.Nonterminal("binop2")])

    binop2 = g.addRule("binop2", [g.Nonterminal("binop3"), g.Nonterminal("binop2_lst",modifier="any")])
    binop2_lst = g.addRule("binop2_lst", [g.TermString("*"), g.Nonterminal("binop3")])
    binop2_lst.add(                      [g.TermString("/"), g.Nonterminal("binop3")])

    binop3 = g.addRule("binop3", [g.Nonterminal("binop4"), g.Nonterminal("binop3_lst",modifier="any")])
    binop3_lst = g.addRule("binop3_lst", [g.TermString("@"), g.Nonterminal("binop4")])

    binop4 = g.addRule("binop4", [g.Nonterminal("ident"), g.TermString("!"), g.Nonterminal("atom")])
    binop4.add(                  [g.Nonterminal("atom")])

    atom = g.addRule("atom", [g.TermSet(set("0123456789"),modifier="some",tag="num")])
    atom.add(                [g.TermString("true", tag="bool")])
    atom.add(                [g.TermString("false", tag="bool")])
    atom.add(                [g.Nonterminal("ident")])
    atom.add(                [g.Nonterminal("str_lit")])
    atom.add(                [g.Nonterminal("set")])
    atom.add(                [g.Nonterminal("map")])
    atom.add(                [g.Nonterminal("order")])
    atom.add(                [g.Nonterminal("record")])
    atom.add(                [g.TermString("("), g.Nonterminal("expr"), g.TermString(")")])

    aset = g.addRule("set",    [g.TermString('{'), g.Nonterminal("elem_lst", modifier="optional"), g.TermString('}')])
    aord = g.addRule("order",  [g.TermString('['), g.Nonterminal("elem_lst", modifier="optional"), g.TermString(']')])
    amap = g.addRule("map",    [g.TermString('{'), g.Nonterminal("elem_kv",  modifier="some"),  g.TermString('}')])
    amap.add(                  [g.TermString('{'), g.TermString(':'), g.TermString('}')])
    arec = g.addRule("record", [g.TermString('['), g.Nonterminal("elem_iv", modifier="some"), g.TermString(']')])

    g.addRule("elem_kv",  [g.Nonterminal("expr"),
                           g.TermString(":"),
                           g.Nonterminal("expr"),
                           g.TermString(",", modifier="optional")])
    g.addRule("elem_iv",  [g.Nonterminal("ident"),
                           g.TermString(":"),
                           g.Nonterminal("expr"),
                           g.TermString(",", modifier="optional")])
    g.addRule("elem_lst", [g.Nonterminal("repeat_elem", modifier="any"), g.Nonterminal("final_elem")])
    g.addRule("repeat_elem", [g.Nonterminal("expr"), g.Glue(), g.TermSet(set(", \r\t\n"))] )
    g.addRule("final_elem", [g.Nonterminal("expr"), g.Glue(), g.TermSet(set(", \r\t\n"), modifier="optional")] )

    str_lit = g.addRule("str_lit", [g.TermString("'"), g.Glue(),
                                    g.TermSet(set('"'), modifier="any", inverse=True), g.Glue(),
                                    g.TermString('"')])
    str_lit.add(                   [g.TermString("u("), g.Glue(),
                                    g.TermSet(set(')'), modifier="any", inverse=True), g.Glue(),
                                    g.TermString(')')])

    letters = string.ascii_lowercase + string.ascii_uppercase
    ident = g.addRule("ident", [g.TermSet(set("_"+letters),tag="ident"), g.Glue(),
                                g.TermSet(set("_"+letters+string.digits), modifier="any"),
                                g.Remover()])
    return g


def stage2(tree):
    result = Grammar(tree.children[0].key.content)
    functors = { 'T':      (lambda a: result.TermSet(a) if isinstance(a,set) else result.TermString(a)),
                 'TA':     (lambda a: result.TermSet(a,"any") if isinstance(a,set) else result.TermString(a,"any")),
                 'TAN':    (lambda a: result.TermSet(a,"some",modifier="any",inverse=True)),
                 'TS':     (lambda a: result.TermSet(a,"some") if isinstance(a,set) else result.TermString(a,"some")),
                 'TO':     (lambda a: result.TermSet(a,"optional") if isinstance(a,set) else result.TermString(a,"optional")),
                 'N':      (lambda a: result.Nonterminal(a)),
                 'NO':     (lambda a: result.Nonterminal(a,modifier="optional")),
                 'NA':     (lambda a: result.Nonterminal(a,modifier="any")),
                 'NS':     (lambda a: result.Nonterminal(a,modifier="some")),
                 'G':      (lambda a: result.Glue()),
                 'R':      (lambda a: result.Remover())
               }
    functors2 = { 'T':      (lambda a: result.Terminal(a['chars'],tag=a['tag'])),
                  'TS':     (lambda a: result.Terminal(a['chars'],"some", tag=a['tag'])),
                }
    def unbox(v):
        if isinstance(v,AST.StringLit):
            return v.content
        if isinstance(v,AST.Set):
            return set(unbox(c) for c in v.children)
        if isinstance(v,AST.Record):
            return {k:unbox(v) for k,v in v.record.items()}
        assert False, v
    def symbol(call):
        if isinstance(call.arg,AST.StringLit) or isinstance(call.arg,AST.Set):
            return functors[call.function.content](unbox(call.arg))
        if isinstance(call.arg,AST.Record):
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

class AST:
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
            assert isinstance(key,AST.Ident), key
            self.key = key.content
            self.value = value
        def __str__(self):
            return f"{self.key}:{self.value}"


def onlyElemList(node):
    return isinstance(node.children[1],Parser.Nonterminal) and node.children[1].tag=='elem_lst'
ntTransformer = {
    'str_lit' :     (lambda node: AST.StringLit(node.children[1].chars)),
    'ident':        (lambda node: AST.Ident(node.children[0].content+"".join([c.chars for c in node.children[1:]]))),
    'binop4':       (lambda node: AST.Call(node.children[0], node.children[2])),
    'final_elem':   (lambda node: node.children[0]),
    'repeat_elem':  (lambda node: node.children[0]),
    'order':        (lambda node: AST.Order(node.children[1].children) if onlyElemList(node)
                             else AST.Order(node.children[1:-1])),
    'set':          (lambda node: AST.Set(node.children[1].children) if onlyElemList(node)
                             else AST.Set(node.children[1:-1])),
    'map':          (lambda node: AST.Map(node.children[1:-1])),
    'record':       (lambda node: AST.Record(node.children[1:-1])),
    'elem_kv':      (lambda node: AST.KeyVal(node.children[0], node.children[2])),
    'elem_iv':      (lambda node: AST.IdentVal(node.children[0], node.children[2]))
}
tTransformer = {
    'ident':        (lambda node: AST.Ident(node.chars)),
    'num':          (lambda node: AST.NumberLit(node.chars)),
}

def buildCommon():
    stage1g = stage1()
    parser = Parser(stage1g, stage1g.discard, ntTransformer=ntTransformer, tTransformer=tTransformer)
    return stage1g, parser

def buildGrammar():
    _, parser = buildCommon()
    return stage2(next(parser.parse(grammar)))

def buildPidginParser(trace=None, start='expr'):
    dir= os.path.dirname(__file__)
    grammar = open(os.path.join(dir, "grammar.g")).read()
    stage1g, parser = buildCommon()
    stage2g = stage2(next(parser.parse(grammar, trace=trace)))
    stage2g.start = start
    return Parser(stage2g, stage1g.discard, ntTransformer=ntTransformer, tTransformer=tTransformer)

def buildParser(grammar, discard=None):
    return Parser(grammar, discard, ntTransformer=ntTransformer, tTransformer=tTransformer)

