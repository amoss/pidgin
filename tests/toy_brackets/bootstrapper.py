import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from bootstrap.graph import Graph
from bootstrap.grammar import Grammar


def build():
    '''
    Cleanest expression of the brackets language in the grammar.
    lst <- expr+
    expr <- ( expr* )
    '''
    g = Grammar("lst")
    g.addRule("expr", [g.Terminal("("), g.Nonterminal("expr","any"), g.Terminal(")")])
    g.addRule("lst",  [g.Nonterminal("expr","some")])
    graph = g.build()
    return g, graph
