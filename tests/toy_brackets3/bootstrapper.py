import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from bootstrap.graph import Graph
from bootstrap.grammar import Grammar


def build():
    '''
    Variation with explicit recursion on both rules, left-recursive form.
    lst <- lst pair
          | pair
    pair <- ( )
          | ( lst )
    '''
    g = Grammar("lst")
    lst = g.addRule("lst", [g.Nonterminal("lst"), g.Nonterminal("pair")])
    lst.add(               [g.Nonterminal("lst")])
    pair = g.addRule("pair", [g.Terminal("("), g.Terminal(")")])
    pair.add(                [g.Terminal("("), g.Nonterminal("lst"), g.Terminal(")")])
    graph = g.build()
    return g, graph
