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

def build():
    '''
    Simple quoted strings (no escapes)
    '''
    g = Grammar("quoted")
    quoted = g.addRule("quoted", [g.Terminal('"'), g.Terminal(set(['"']), "any", inverse=True), g.Terminal('"')])
    graph = g.build()
    return g, graph
