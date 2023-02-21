# Copyright (C) 2003 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from bootstrap.graph import Graph
from bootstrap.grammar import Grammar

def anyPrefixOf(s):
    for i in range(1, len(s)):
        yield s[:i]

brackets = ( ("(",")"), ("[","]"), ("{","}"), ("<",">") )

def build():
    '''
    The subset of the pidgin expression grammar that handles constants with the weird and wonderful bracketing.
    lst <- expr+
    expr <- ( expr* )
    '''
    g = Grammar("const")
    const = g.addRule("const", [g.Terminal(set("0123456789"),"some")])
    for p in anyPrefixOf("unicode"):
        for l,r in brackets:
            const.add(         [g.Terminal(p), g.Terminal(l), g.Terminal(set([r]), "any", inverse=True), g.Terminal(r)])
    graph = g.build()
    return g, graph
