# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from bootstrap.grammar import Grammar


def build():
    '''
    No precedence or associativity encoded in operator
    expr <- x | expr + expr
    '''
    g = Grammar("expr")
    lst = g.addRule("expr", [g.Terminal("x")])
    lst.add(                [g.Nonterminal("expr"), g.Terminal("+"), g.Nonterminal("expr")])

    return g

# The spot for manual testing of the parser
if __name__=="__main__":
    grammar = build()
    from bootstrap.parser import Parser
    parser = Parser(grammar, discard=grammar.discard)
    res = (list(parser.parse("x+x+x+x",trace=open("trace.dot","wt"))))
    print(res)
    res[0].dump()
