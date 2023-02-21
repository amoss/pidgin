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
    Variation with explicit recursion on bottom rule, recursive form is bounded.
    lst  <- expr+
    expr <- ( ) | ( list )
    '''
    g = Grammar("lst")
    lst = g.addRule("lst", [g.Nonterminal("expr","some")])
    expr = g.addRule("expr", [g.Terminal("("), g.Terminal(")")])
    expr.add(                [g.Terminal("("), g.Nonterminal("lst","just"), g.Terminal(")")])
    graph = g.build()
    return g, graph

