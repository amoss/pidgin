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
    Variation with explicit recursion on both rules, right-recursive form.
    lst <- pair lst
          | pair
    pair <- ( )
          | ( lst )
    '''
    g = Grammar("lst")
    lst = g.addRule("lst", [g.Nonterminal("pair"), g.Nonterminal("lst")])
    lst.add(               [g.Nonterminal("pair")])
    pair = g.addRule("pair", [g.Terminal("("), g.Terminal(")")])
    pair.add(                [g.Terminal("("), g.Nonterminal("lst"), g.Terminal(")")])
    graph = g.build()
    return g, graph

