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
    The part of the pidgin grammar that describes sequences, with strings and identifiers.
    '''
    g = Grammar("atom")
    g.setDiscard(g.Terminal(set(" \t\r\n"), "some"))

    atom = g.addRule("atom", [g.Terminal(set("0123456789"),"some")])
    atom.add(                [g.Nonterminal("order")])

    aord = g.addRule("order", [g.Terminal('['), g.Nonterminal("atom", "optional"), g.Terminal(']')])

    return g

# The spot for manual testing of the parser
if __name__=="__main__":
    grammar = build()
    from bootstrap.parser import Parser
    parser = Parser(grammar, discard=grammar.discard)
    parser.dotAutomaton(open("lr0.dot","wt"))
    res = (list(parser.parse("[22 2]",trace=open("trace.dot","wt"))))
    #res = (list(parser.parse("[T!u('), TAN!u(\") ]",trace=open("trace.dot","wt"))))
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
