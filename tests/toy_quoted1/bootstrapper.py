# Copyright (C) 2003 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from bootstrap.graph import Graph
from bootstrap.grammar import Grammar

def anyPrefixOf(s):
    for i in range(1, len(s)):
        yield s[:i]

def build():
    '''
    Simple quoted strings (no escapes)
    '''
    g = Grammar("quoted")
    quoted = g.addRule("quoted", [g.Terminal('"'),
                                  g.Terminal(set(['"']), internal="some", external="optional", inverse=True),
                                  g.Terminal('"')])
    graph = g.build()
    return g, graph

# The spot for manual testing of the parser
#if __name__=="__main__":
#    grammar, graph = build()
#    from bootstrap.parser2 import Parser
#    parser = Parser(graph, discard=grammar.discard)
#    res = (list(parser.parse('"hello"',trace=open("trace.dot","wt"))))
#    for r in res:
#        r.dump()

# The spot for manual testing of the generator
if __name__=="__main__":
    import itertools
    from bootstrap.generator2 import Generator
    grammar, graph = build()
    generator = Generator(grammar)
    sentences = list(generator.step(trace=open("trace.dot","wt")))
    with open("generated.txt","wt") as outputFile:
        for s in sentences:
            s = [ symb.string if symb.string is not None else ("^" if symb.inverse else "") + list(symb.chars)[0] for symb in s]
            outputFile.write("".join(s))
            outputFile.write("\n")
