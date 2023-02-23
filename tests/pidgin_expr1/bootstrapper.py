# Copyright (C) 2003 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

import string
from bootstrap.graph import Graph
from bootstrap.grammar import Grammar

def anyPrefixOf(s):
    for i in range(1, len(s)+1):
        yield s[:i]

brackets = ( ("(",")"), ("[","]"), ("{","}"), ("<",">") )

def build():
    '''
    The subset of the pidgin expression grammar that handles expressions with the weird and wonderful bracketing.
    '''
    g = Grammar("expr")
    g.setDiscard(g.Terminal(set(" \t\r\n"), "some"))
    expr = g.addRule("expr", [g.Terminal(set("0123456789"),"some")])
    expr.add([g.Terminal("true")])
    expr.add([g.Terminal("false")])
    expr.add([g.Nonterminal("ident")])
    for p in anyPrefixOf("unicode"):
        for l,r in brackets:
            expr.add(         [g.Terminal(p, sticky=True), g.Terminal(l, sticky=True),
                               g.Terminal(set([l,r]), "some", inverse=True, sticky=True, external="optional"),
                               g.Terminal(r)])

    for p in anyPrefixOf("order"):
        for l,r in brackets:
            expr.add(         [g.Terminal(p, sticky=True), g.Terminal(l), g.Nonterminal("expr_lst", "any"), g.Terminal(r)])

    for p in anyPrefixOf("set"):
        for l,r in brackets:
            expr.add(         [g.Terminal(p, sticky=True), g.Terminal(l), g.Nonterminal("expr_lst", "any"), g.Terminal(r)])

    for p in anyPrefixOf("map"):
        for l,r in brackets:
            expr.add(         [g.Terminal(p, sticky=True), g.Terminal(l), g.Nonterminal("expr_kv", "any"), g.Terminal(r)])

    const_kv = g.addRule("expr_kv",  [g.Nonterminal("expr"),
                                      g.Terminal(":"),
                                      g.Nonterminal("expr"),
                                      g.Terminal(",", external="optional")])
    expr_lst = g.addRule("expr_lst", [g.Nonterminal("expr"), g.Terminal(",", external="optional")])

    for op in (".-", "-.", ".+", "+.", "*", "/", "+", "-", "@"):
        expr.add([g.Nonterminal("expr"), g.Terminal(op), g.Nonterminal("expr")])

    letters = string.ascii_lowercase + string.ascii_uppercase
    ident = g.addRule("ident", [g.Terminal(set("_"+letters),"just", sticky=True),
                                g.Terminal(set("_"+letters+string.digits), "some", external="optional")])


    graph = g.build()
    return g, graph

# The spot for manual testing of the parser
if __name__=="__main__":
    grammar, graph = build()
    from bootstrap.parser2 import Parser
    parser = Parser(graph, discard=grammar.discard)
    res = (list(parser.parse("uni[true]+true",trace=open("trace.dot","wt"))))
    for r in res:
        r.dump()

# The spot for manual testing of the generator
#if __name__=="__main__":
#    import itertools
#    from bootstrap.generator2 import Generator
#    grammar, graph = build()
#    generator = Generator(grammar)
#    sentences = list(itertools.islice(generator.step(), 2000))
#    with open("generated.txt","wt") as outputFile:
#        for s in sentences:
#            s = [ symb.string if symb.string is not None else list(symb.chars)[0] for symb in s]
#            outputFile.write("".join(s))
#            outputFile.write("\n")
