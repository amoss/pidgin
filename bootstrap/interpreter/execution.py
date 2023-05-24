# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from ..util import dump
from .frontend import AST
from ..parser import Token

class Environment:
    def __init__(self):
        self.values = {}
        self.types = {}

    def contains(self, name):
        return name in self.values

    def insert(self, name, valueType, value):
        self.values[name] = value
        self.types[name] = valueType

    def dump(self):
        for name in self.values.keys():
            print(f'{name} {self.types[name]} : {self.values[name]}')


def processDeclaration(node, env):
    print(f'exec decl {node}')
    assert not env.contains(node.name), node.name
    env.insert(node.name, "func", node)

def executeAssignment(node, env):
    print(f'execute = {node}')

def executeStatement(node, env):
    print(f'exec stmt {node}')
    if len(node.children)==3  and  node.children[1].symbol.isTerminal  and node.children[1].span=='=':
        executeAssignment(node, env)
    else:
        dump(node)

# Temporary structure to bootstrap development. Later we will convert the AST for statements to a graph
# for the basic block and rework execution around that.
def execute(node, env):
    assert node.symbol.isNonterminal, node
    if node.symbol.name == 'program':
        for child in node.children:
            if isinstance(child, AST.FunctionDecl):
                processDeclaration(child,env)
        for child in node.children:
            if isinstance(child, Token)  and  child.symbol.name == 'statement':
                executeStatement(child, env)

