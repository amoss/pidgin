# Copyright (C) 2003 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
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
    g = Grammar("expr")
    g.setDiscard(g.Terminal(set(" \t\r\n"), "some"))

    expr = g.addRule("expr", [g.Nonterminal("ident"), g.Terminal("!"), g.Nonterminal("atom")])
    expr.add(                [g.Nonterminal("atom")])

    atom = g.addRule("atom", [g.Nonterminal("str_lit")])
    atom.add(                [g.Nonterminal("ident")])
    atom.add(                [g.Nonterminal("set")])
    atom.add(                [g.Nonterminal("map")])
    atom.add(                [g.Nonterminal("order")])
    atom.add(                [g.Terminal("("), g.Nonterminal("expr"), g.Terminal(")")])

    aset = g.addRule("set",   [g.Terminal('{'), g.Nonterminal("elem_lst", "optional"), g.Terminal('}')])
    aord = g.addRule("order", [g.Terminal('['), g.Nonterminal("elem_lst", "optional"), g.Terminal(']')])
    amap = g.addRule("map",   [g.Terminal('{'), g.Nonterminal("elem_kv",  "some"),  g.Terminal('}')])
    amap.add(                 [g.Terminal('{'), g.Terminal(':'), g.Terminal('}')])

    g.addRule("elem_kv",  [g.Nonterminal("expr"),
                           g.Terminal(":"),
                           g.Nonterminal("expr"),
                           g.Terminal(",", external="optional")])
    g.addRule("elem_lst", [g.Nonterminal("repeat_elem", "any"), g.Nonterminal("final_elem")])
    g.addRule("repeat_elem", [g.Nonterminal("expr"), g.Glue(), g.Terminal(set(", \r\t\n"))] )
    g.addRule("final_elem", [g.Nonterminal("expr"), g.Glue(), g.Terminal(set(", \r\t\n"), external="optional")] )

    str_lit = g.addRule("str_lit", [g.Terminal("'"), g.Glue(),
                                    g.Terminal(set('"'), "some", inverse=True, external="optional"), g.Glue(),
                                    g.Terminal('"')])
    str_lit.add(                   [g.Terminal("u("), g.Glue(),
                                    g.Terminal(set(')'), "some", inverse=True, external="optional"), g.Glue(),
                                    g.Terminal(')')])

    letters = string.ascii_lowercase + string.ascii_uppercase
    ident = g.addRule("ident", [g.Terminal(set("_"+letters),"just", sticky=True),
                                g.Terminal(set("_"+letters+string.digits), "some", external="optional")])

    return g

# The spot for manual testing of the parser
if __name__=="__main__":
    grammar = build()
    from bootstrap.parser import Parser
    parser = Parser(grammar, discard=grammar.discard)
    parser.dotAutomaton(open("lr0.dot","wt"))
    res = (list(parser.parse("[T ! u ('), TAN!u(\") T!u('), TAN!u(\") ]",trace=open("trace.dot","wt"))))
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
