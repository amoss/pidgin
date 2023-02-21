# Copyright (C) 2003 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from bootstrap.graph import Graph
from bootstrap.grammar import Grammar

def anyPrefixOf(s):
    for i in range(1, len(s)+1):
        yield s[:i]

brackets = ( ("(",")"), ("[","]"), ("{","}"), ("<",">") )

def build():
    '''
    The subset of the pidgin expression grammar that handles constants with the weird and wonderful bracketing.
    lst <- expr+
    expr <- ( expr* )
    '''
    g = Grammar("const")
    const = g.addRule("const", [g.Terminal(set("0123456789"),"some")])
    for p in anyPrefixOf("unicode"):
        for l,r in brackets:
            const.add(         [g.Terminal(p), g.Terminal(l), g.Terminal(set([l,r]), "any", inverse=True), g.Terminal(r)])

    for p in anyPrefixOf("order"):
        for l,r in brackets:
            const.add(         [g.Terminal(p), g.Terminal(l), g.Nonterminal("const", "any"), g.Terminal(r)])

    for p in anyPrefixOf("set"):
        for l,r in brackets:
            const.add(         [g.Terminal(p), g.Terminal(l), g.Nonterminal("const", "any"), g.Terminal(r)])

    for p in anyPrefixOf("map"):
        for l,r in brackets:
            const.add(         [g.Terminal(p), g.Terminal(l), g.Nonterminal("const_kv", "any"), g.Terminal(r)])

    const_kv = g.addRule("const_kv", [g.Nonterminal("const"), g.Terminal(":"), g.Nonterminal("const")])

    graph = g.build()
    return g, graph

# The spot for manual testing of the parser
# if __name__=="__main__":
#    grammar, graph = build()
#    from bootstrap.parser2 import Parser
#    parser = Parser(graph)
#    print(list(parser.parse("unicode[öäå123]")))

# The spot for manual testing of the generator
if __name__=="__main__":
    import itertools
    from bootstrap.generator2 import Generator
    grammar, graph = build()
    generator = Generator(grammar)
    sentences = list(itertools.islice(generator.step(), 2000))
    with open("generated.txt","wt") as outputFile:
        for s in sentences:
            s = [ symb.string if symb.string is not None else list(symb.chars)[0] for symb in s]
            outputFile.write("".join(s))
            outputFile.write("\n")
