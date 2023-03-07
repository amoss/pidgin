# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

import string
from bootstrap.grammar import Grammar

brackets = ( ("(",")"), ("[","]"), ("{","}"), ("<",">") )

def build():
    '''
    Just the part of the pidgin grammar that describes set and map literals with numbers as atoms.
    This is the original broken formulation (bad interaction between optional components and the
    discard channel). The fixed version is toy_setmaplist2.
    '''
    g = Grammar("atom")
    g.setDiscard(g.Terminal(set(" \t\r\n"), "some"))

    atom = g.addRule("atom", [g.Terminal(set("0123456789"),"some")])
    atom.add(                [g.Nonterminal("set")])
    atom.add(                [g.Nonterminal("map")])

    aset = g.addRule("set",   [g.Terminal('{'), g.Nonterminal("expr_lst", "any"), g.Terminal('}')])
    aord = g.addRule("order", [g.Terminal('['), g.Nonterminal("expr_lst", "any"), g.Terminal(']')])
    amap = g.addRule("map",   [g.Terminal('{'), g.Nonterminal("expr_kv",  "some"),  g.Terminal('}')])
    amap.add(                 [g.Terminal('{'), g.Terminal(':'), g.Terminal('}')])

    g.addRule("expr_kv",  [g.Nonterminal("atom"),
                           g.Terminal(":"),
                           g.Nonterminal("atom"),
                           g.Terminal(",", external="optional")])
    g.addRule("expr_lst", [g.Nonterminal("atom"), g.Terminal(",", external="optional")])

    return g

# The spot for manual testing of the parser
if __name__=="__main__":
    grammar = build()
    from bootstrap.parser import Parser
    parser = Parser(grammar, discard=grammar.discard)
    parser.dotAutomaton(open("lr0.dot","wt"))
    res = (list(parser.parse("{2:3 22 5:4}",trace=open("trace.dot","wt"))))
    for r in res:
        r.dump()

# The spot for manual testing of the generator
#if __name__=="__main__":
#    import itertools
#    from bootstrap.generator import Generator
#    grammar, graph = build()
#    generator = Generator(grammar)
#    sentences = list(itertools.islice(generator.step(), 2000))
#    with open("generated.txt","wt") as outputFile:
#        for s in sentences:
#            s = [ symb.string if symb.string is not None else list(symb.chars)[0] for symb in s]
#            outputFile.write("".join(s))
#            outputFile.write("\n")
