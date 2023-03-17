# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from bootstrap.grammar import Grammar


def build():
    g = Grammar("seq")
    seq = g.addRule("seq", [g.Nonterminal("bounded"), g.TermSet(set(['y','z'])), g.TermSet(set(['y','z']))])
    seq.add(               [g.TermString('u'), g.Nonterminal("unbounded"), g.TermSet(set(['y','z'])), g.TermSet(set(['y','z']))])
    g.addRule("bounded",   [g.Nonterminal("bounded2",strength="greedy", modifier="some")])
    g.addRule("bounded2",  [g.Nonterminal("bounded3",strength="greedy", modifier="any"), g.TermString("b")])
    g.addRule("bounded3",  [g.TermSet(set(['x','y']))])
    g.addRule("unbounded",   [g.Nonterminal("unbounded2",strength="greedy", modifier="some")])
    g.addRule("unbounded2",  [g.Nonterminal("unbounded3",strength="greedy", modifier="any")])
    g.addRule("unbounded3",  [g.TermSet(set(['x','y']))])
    return g

# The spot for manual testing of the parser
if __name__=="__main__":
    grammar = build()
    from bootstrap.parser import Parser
    parser = Parser(grammar, discard=grammar.discard)
    parser.dotAutomaton(open("lr0.dot","wt"))
    res = (list(parser.parse('uxzz',trace=open("trace.dot","wt"))))
    for r in res:
        r.dump()
