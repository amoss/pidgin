import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from bootstrap.graph import Graph
from bootstrap.grammar import Grammar


def build():
    '''
    Variation with .... bollocks
    expr <- ( )
          | ( expr+ )
    '''
    g = Grammar("expr")
    expr = g.addRule("expr", [g.Terminal("("), g.Terminal(")")])
    expr.add(                [g.Terminal("("), g.Nonterminal("expr","any"), g.Terminal(")")])
    graph = g.build()
    return g, graph
