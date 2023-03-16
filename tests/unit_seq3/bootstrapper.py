# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from bootstrap.grammar import Grammar


def build():
    g = Grammar("seq")
    g.addRule("seq", [g.Nonterminal("ntx","any")])
    g.addRule("ntx", [g.TermString("x")])

    return g

# The spot for manual testing of the parser
if __name__=="__main__":
    grammar = build()
    from bootstrap.parser import Parser
    parser = Parser(grammar, discard=grammar.discard)
    parser.dotAutomaton(open("lr0.dot","wt"))
    res = (list(parser.parse('xxx',trace=open("trace.dot","wt"))))
    for r in res:
        r.dump()
