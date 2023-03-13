# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os, sys
rootDir= os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

import argparse
import string
import sys

from bootstrap.parser import Parser
from bootstrap.grammar import Grammar
from bootstrap.interpreter import buildParser, AST

def dump(node, depth=0):
    print(f"{'  '*depth}{type(node)}{node}")
    if hasattr(node,'children'):
        for c in node.children:
            dump(c,depth+1)

# The spot for manual testing of second-stage parsers
if __name__=="__main__":
    argParser = argparse.ArgumentParser()
    argParser.add_argument("grammar")
    argParser.add_argument("-i", "--input")
    argParser.add_argument("-f", "--file")
    argParser.add_argument("-d", "--debug", action="store_true")
    args = argParser.parse_args()

    source = open(args.grammar).read()
    parser = buildParser(trace=open("trace.dot","wt"))
    if args.debug:  parser.grammar.dump()
    parser.dotAutomaton(open("lr0.dot","wt"))
    if args.input is not None:
        res2 = list(parser.parse(args.input, trace=open('trace2.dot','wt')))
    if args.file is not None:
        res2 = list(parser.parse(open(args.file).read(), trace=open('trace2.dot','wt')))
    print(f"\nResults {len(res2)}:")
    for r in res2:
        dump(r)




