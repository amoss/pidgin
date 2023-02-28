# Copyright (C) 2003 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from bootstrap.grammar import Grammar


def build():
    '''
    Simple way to provoke ambiguity - list of xs can reduced by iteration or recursion.
    lst <- x | x lst*
    '''
    g = Grammar("lst")
    lst = g.addRule("lst", [g.Terminal("x")])
    lst.add(               [g.Terminal("x"), g.Nonterminal("lst","any")])

    return g
