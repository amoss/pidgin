# Copyright (C) 2003 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from bootstrap.graph import Graph
from bootstrap.grammar import Grammar


def build():
    '''
    No precedence or associativity encoded in operator
    expr <- x | expr + expr
    '''
    g = Grammar("expr")
    lst = g.addRule("expr", [g.Terminal("x")])
    lst.add(                [g.Nonterminal("expr"), g.Terminal("+"), g.Nonterminal("expr")])

    graph = g.build()
    return g, graph

# The spot for manual testing of the parser
if __name__=="__main__":
    grammar, graph = build()
    from bootstrap.parser2 import Parser
    parser = Parser(graph, discard=grammar.discard)
    res = (list(parser.parse("x+x+x+x",trace=open("trace.dot","wt"))))
    print(res)
    res[0].dump()
