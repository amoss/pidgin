# Copyright (C) 2003 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from bootstrap.grammar import Grammar


def build():
    '''
    Variation with explicit recursion on top rule, left-recursive form.
    lst  <- expr | lst expr
    expr <- ( expr* )
    '''
    g = Grammar("lst")
    lst = g.addRule("lst", [g.Nonterminal("expr")])
    lst.add(               [g.Nonterminal("lst"), g.Nonterminal("expr")])
    expr = g.addRule("expr", [g.Terminal("("), g.Nonterminal("expr","any"), g.Terminal(")")])
    return g

