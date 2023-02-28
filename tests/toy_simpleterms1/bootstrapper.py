# Copyright (C) 2003 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from bootstrap.grammar import Grammar


def build():
    '''
    Simple expression grammar to match fig3.37 in Grune et al, allowing comparison with fig3.41.
    expr <- term | expr + term
    term <- x | ( expr )

    '''
    g = Grammar("expr")
    expr = g.addRule("expr", [g.Nonterminal("term")])
    expr.add(                [g.Nonterminal("expr"), g.Terminal("+"), g.Nonterminal("term")])
    term = g.addRule("term", [g.Terminal("x")])
    term.add(                [g.Terminal("("), g.Nonterminal("expr"), g.Terminal(")")])
    return g

# The spot for manual testing of the parser
if __name__=="__main__":
    grammar = build()
    #graph.dot(open("tree.dot","wt"))
    from bootstrap.parser2 import Parser2
    parser = Parser2(grammar, discard=grammar.discard)
    parser.dotAutomaton(open("lr0.dot","wt"))
    res = (list(parser.parse("x+(x+x)",trace=open("trace.dot","wt"))))
    for r in res:
        print("Result:")
        r.dump()
