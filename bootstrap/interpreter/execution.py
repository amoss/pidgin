# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from ..util import dump
from .frontend import AST
from .box import Box, Type
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

    def lookup(self, name):
        return self.values[name], self.types[name]

    def dump(self):
        for name in self.values.keys():
            print(f'{name} {self.types[name]} : {self.values[name]}')


def processDeclaration(node, env):
    print(f'exec decl {node}')
    assert not env.contains(node.name), node.name
    env.insert(node.name, "func", node)

def executeAssignment(node, env):
    print(f'execute = {node}')
    try:
        box = evaluate(node.children[2], env)
    except:
        raise

def executeStatement(node, env):
    print(f'exec stmt {node}')
    if len(node.children)==3  and  node.children[1].symbol.isTerminal  and node.children[1].span=='=':
        executeAssignment(node, env)
    else:
        dump(node)

# Temporary structure to bootstrap development. Later we will convert the AST for statements to a graph
# for the basic block and rework execution around that.
def execute(node, env):
    if isinstance(node, AST.FunctionDecl):
        for stmt in node.body:
            if isinstance(stmt, AST.FunctionDecl):
                processDeclaration(stmt,env)
        for stmt in node.body:
            if isinstance(stmt, Token)  and stmt.symbol.name == 'statement':
                executeStatement(stmt, env)
        return
    assert node.symbol.isNonterminal, node
    if node.symbol.name == 'program':
        for child in node.children:
            if isinstance(child, AST.FunctionDecl):
                processDeclaration(child,env)
        for child in node.children:
            if isinstance(child, Token)  and  child.symbol.name == 'statement':
                executeStatement(child, env)


def evaluate(node, env=None):
    '''Evaluate the expression in the AST *node*, if the *env* is None then the expression must
       be constant and will throw if it depends on a non-constant value.'''
    if isinstance(node, AST.NumberLit):
        return Box(Type('N'), node.content)
    if isinstance(node, AST.StringLit):
        return Box(Type('S'), node.content)
    if isinstance(node, AST.Order):
        return Box.evaluateOrder(node, env)
    if isinstance(node, AST.Set):
        return Box.evaluateSet(node, env)
    if isinstance(node, AST.Ident):
        assert env is not None, f"{node} can't be in constant expression"
        return env.lookup(node)
    if isinstance(node, AST.Call):
        assert env.contains(node.function), node.function
        function, fType = env.lookup(node.function)
        assert fType=="func", fType
        print(f'call arg={node.arg} func={function}')
        callEnv = Environment()
        assert isinstance(node.arg, AST.Record), node.arg
        for name,value in node.arg.record.items():
            callEnv.insert(name, "evaluate type", evaluate(value))
        dump(function)
        execute(function, callEnv)
    despatch = {
        'binop1': Box.evaluateBinop1,
        'binop2': Box.evaluateBinop2
    }
    assert isinstance(node, Token) and node.symbol.isNonterminal, node
    assert node.tag in despatch, node.tag
    return despatch[node.tag](node, env)
