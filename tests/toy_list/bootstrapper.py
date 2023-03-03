# Copyright (C) 2003 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from bootstrap.grammar import Grammar


def build():
    '''
    Simple list of terms

    '''
    g = Grammar("expr")
    g.setDiscard(g.Terminal(set(" \t\r\n"), "some"))

    expr = g.addRule("expr", [g.Terminal("["), g.Nonterminal("term", "any"), g.Terminal("]")])
    term = g.addRule("term", [g.Terminal("x")])
    return g

# The spot for manual testing of the parser
if __name__=="__main__":
    grammar = build()
    #graph.dot(open("tree.dot","wt"))
    from bootstrap.parser import Parser
    parser = Parser(grammar, discard=grammar.discard)
    parser.dotAutomaton(open("lr0.dot","wt"))
    res = (list(parser.parse("[x x]",trace=open("trace.dot","wt"))))
    for r in res:
        print("Result:")
        r.dump()
