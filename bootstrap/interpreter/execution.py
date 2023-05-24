# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from ..util import dump

class Environment:
    pass

def processDeclaration(node, env):
    print(f'exec decl {node}')

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
            if child.symbol.name=='decl':
                processDeclaration(child,env)
        for child in node.children:
            if child.symbol.name == 'statement':
                executeStatement(child, env)

