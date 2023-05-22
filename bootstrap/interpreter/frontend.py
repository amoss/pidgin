# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import string

from ..grammar import Grammar
from ..parser import Parser, Token
from ..machine import Automaton
from ..util import dump

def stage1():
    def T(val, m=None, s=None):
        if m is None:
            if isinstance(val,str):
                return Grammar.TermString(val)
            return Grammar.TermSet(val)
        if isinstance(val,str):
            return Grammar.TermString(val, modifier=m)
        return Grammar.TermSet(val, modifier=m, strength=s)

    def S(val, invert=False, m=None, s=None):
        if m is None:
            return Grammar.TermSet(val,inverse=invert)
        if s is None:
            return Grammar.TermSet(val,inverse=invert,modifier=m)
        return Grammar.TermSet(val,inverse=invert,modifier=m,strength=s)


    def N(name, m='just', s='greedy'):
        return Grammar.Nonterminal(name, modifier=m, strength=s)

    def Glue():
        return Grammar.Glue()

    def Remove():
        return Grammar.Remover()

    '''The largest subset of pidgin so far (currently exprs + records).'''
    letters = string.ascii_lowercase + string.ascii_uppercase
    g = Grammar('binop1')
    g.setDiscard(S(' \t\r\n',m='some'))
    g.addRule('binop1', [N('binop2'), N('binop1_lst',m='any')])
    g.addRule('binop1_lst', [T('.+'), N('binop2')],
                            [T('+.'), N('binop2')],
                            [T('.-'), N('binop2')],
                            [T('-.'), N('binop2')],
                            [T('+'),  N('binop2')],
                            [T('-'),  N('binop2')])
    g.addRule('binop2', [N('binop3'), N('binop2_lst',m='any')])
    g.addRule('binop2_lst', [T('*'), N('binop3')],
                            [T('/'), N('binop3')])
    g.addRule('binop3', [N('binop4'), N('binop3_lst',m='any')])
    g.addRule('binop3_lst', [T('@'), N('binop4')])
    g.addRule('binop4', [N('atom')],
                        [N('ident'), T('!'), N('atom')])

    g.addRule('atom', [T('true')],
                      [T('false')],
                      [S(string.digits), Glue(), S(string.digits,m='any'), Remove()],
                      [N('ident')],
                      [N('str_lit')],
                      [N('set')],
                      [N('map')],
                      [N('record')],
                      [N('order')],
                      [T('('),N('binop1'),T(')')])

    g.addRule('set', [T('{'), T('}')],
                     [T('{'), N('order_pair', m='any'), N('binop1'), T(',',m='optional'), T('}')],
                     [T('{'), N('binop1'), N('binop1', m='some'), T('}')])
    g.addRule('order', [T('['), T(']')],
                       [T('['), N('order_pair', m='any'), N('binop1'), T(',',m='optional'), T(']')],
                       [T('['), N('binop1'), N('binop1', m='some'), T(']')])
    g.addRule('order_pair', [N('binop1'), T(',')])
    g.addRule('record',   [T('['), T(':'), T(']')],
                          [T('['), N('iv_comma',m='any'), N('ident'), T(':'), N('binop1'), T(',',m='optional'), T(']')],
                          [T('['), N('iv_pair'), N('iv_pair',m='some'), T(']')])
    g.addRule('map',   [T('{'), T(':'), T('}')],
                       [T('{'), N('kv_comma',m='any'), N('binop1'), T(':'), N('binop1'), T(',',m='optional'), T('}')],
                       [T('{'), N('kv_pair'), N('kv_pair',m='some'), T('}')])
    g.addRule('iv_pair',  [N('ident'), T(':'), N('binop1')])
    g.addRule('iv_comma',  [N('ident'), T(':'), N('binop1'), T(',')])
    g.addRule('kv_pair',  [N('binop1'), T(':'), N('binop1')])
    g.addRule('kv_comma', [N('binop1'), T(':'), N('binop1'), T(',')])
    g.addRule('str_lit', [T("'"), Glue(), S(['"'],True,m='any'), T('"'), Remove()],
                         [T('<<'), Glue(), N('str_lit2',m='any'), T('>>'), Remove()])
    g.addRule('str_lit2', [S([">"],True)], [T('>'), S([">"],True)])
    g.addRule('ident', [S(list(letters)+['_']), Glue(), S(list(letters+string.digits)+['_'], m='any'), Remove()])
    return g


def stage2(tree):
    result = Grammar(tree.children[0].key.content)
    functors = { 'T':      (lambda a: result.TermSet(a) if isinstance(a,set) else result.TermString(a)),
                 'TA':     (lambda a: result.TermSet(a,"any") if isinstance(a,set) else result.TermString(a,"any")),
                 'TAN':    (lambda a: result.TermSet(a,modifier="any",inverse=True)),
                 'TS':     (lambda a: result.TermSet(a,"some") if isinstance(a,set) else result.TermString(a,"some")),
                 'TO':     (lambda a: result.TermSet(a,"optional") if isinstance(a,set) else result.TermString(a,"optional")),
                 'N':      (lambda a: result.Nonterminal(a)),
                 'NO':     (lambda a: result.Nonterminal(a,modifier="optional")),
                 'NA':     (lambda a: result.Nonterminal(a,modifier="any")),
                 'NS':     (lambda a: result.Nonterminal(a,modifier="some")),
                 'G':      (lambda a: result.Glue()),
                 'R':      (lambda a: result.Remover())
               }
    functors2 = { 'T':      (lambda a: result.TermSet(a['chars'],tag=a['tag']) if isinstance(a['chars'],set) \
                                                                               else result.TermString(a['chars'])),
                  'TA':     (lambda a: result.TermSet(a['chars'],"any", tag=a['tag']) if isinstance(a['chars'],set) \
                                                                                       else result.TermString(a['chars'],"any")),
                  'TS':     (lambda a: result.TermSet(a['chars'],"some", tag=a['tag']) if isinstance(a['chars'],set) \
                                                                                       else result.TermString(a['chars'],"some")),
                }
    def unbox(v):
        if isinstance(v,AST.StringLit):
            return v.content
        if isinstance(v,AST.Set):
            return set(unbox(c) for c in v.elements)
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
            rule = result.addRule(kv.key.content, [symbol(s) for s in kv.value.elements[0].seq])
            for clause in kv.value.elements[1:]:
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
            if isinstance(function, AST.Ident):
                self.function = function
            else:
                self.function = AST.Ident(function.span)
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
            self.elements = children
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


def removeFinalComma(seq):
    if len(seq)==0:   return seq
    final = seq[-1]
    if isinstance(final,Token) and final.span==',':
        return seq[:-1]
    return seq

class SynToken:
    def __init__(self, span):
        self.span = span

def collectSpans(node):
    dump(node)
    return SynToken("".join(n.span for n in node.children))


ntTransformer = {
    'str_lit' :     (lambda node: AST.StringLit("".join(n.span for n in node.children[1:-1] if n is not None))),
#    'str_lit2':     (lambda node: collectSpans(node)),
    'ident':        (lambda node: AST.Ident("".join(n.span for n in node.children))),
    'binop4':       (lambda node: AST.Call(node.children[0], node.children[2])),
#    'final_elem':   (lambda node: node.children[0]),
#    'repeat_elem':  (lambda node: node.children[0]),
    'order':        (lambda node: AST.Order(removeFinalComma(node.children[1:-1]))),
    'set':          (lambda node: AST.Set(removeFinalComma(node.children[1:-1]))),
    'map':          (lambda node: AST.Map(node.children[1:-1])),
    'record':       (lambda node: AST.Record(node.children[1:-1])),
    'kv_pair':      (lambda node: AST.KeyVal(node.children[0], node.children[2])),
    'order_pair':   (lambda node: node.children[0]),
    'comma_pair':   (lambda node: node.children[0]),
    'iv_pair':      (lambda node: AST.IdentVal(node.children[0], node.children[2]))
}

tTransformer = {
    'ident':        (lambda node: AST.Ident(node.span)),
    'num':          (lambda node: AST.NumberLit(node.span)),
}

def buildCommon():
    stage1g = stage1()
    machine = Automaton(stage1g)
    parser = Parser(machine, ntTransformer=ntTransformer, tTransformer=tTransformer)
    return stage1g, machine, parser

def buildGrammar():
    _, parser = buildCommon()
    return stage2(next(parser.execute(grammar)))

def buildPidginParser(trace=None, start='expr'):
    thisDir= os.path.dirname(__file__)
    grammar = open(os.path.join(thisDir, "grammar.g")).read()
    stage1g, stage1m, parser = buildCommon()
    rs = [r for r in parser.execute(grammar,False)]
    #parser.trace.output(open('stage2trace.dot','wt'))
    stage2g = stage2(rs[0])
    stage2g.start = start
    stage2g.discard = stage1g.discard
    stage2m = Automaton(stage2g)
    return Parser(stage2m, ntTransformer=ntTransformer, tTransformer=tTransformer)

def buildParser(grammar):
    return Parser(grammar, ntTransformer=ntTransformer, tTransformer=tTransformer)

