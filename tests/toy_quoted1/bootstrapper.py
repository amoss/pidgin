# Copyright (C) 2003 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from bootstrap.grammar import Grammar

def build():
    '''
    Simple quoted strings (no escapes)
    '''
    g = Grammar("quoted")
    quoted = g.addRule("quoted", [g.Terminal('"'),
                                  g.Terminal(set(['"']), internal="some", external="optional", inverse=True),
                                  g.Terminal('"')])
    return g

# The spot for manual testing of the parser
#if __name__=="__main__":
#    grammar = build()
#    from bootstrap.parser import Parser
#    parser = Parser(grammar, discard=grammar.discard)
#    res = (list(parser.parse('"hello"',trace=open("trace.dot","wt"))))
#    for r in res:
#        r.dump()

# The spot for manual testing of the generator
if __name__=="__main__":
    import itertools
    from bootstrap.generator import Generator
    grammar = build()
    generator = Generator(grammar)
    sentences = list(generator.step(trace=open("trace.dot","wt")))
    with open("generated.txt","wt") as outputFile:
        for s in sentences:
            s = [ symb.string if symb.string is not None else ("^" if symb.inverse else "") + list(symb.chars)[0] for symb in s]
            outputFile.write("".join(s))
            outputFile.write("\n")
