# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

import argparse

from bootstrap.interpreter import buildParser, Box

argParser = argparse.ArgumentParser()
argParser.add_argument("-i", "--input")
argParser.add_argument("-f", "--file")
args = argParser.parse_args()

if args.input is None and args.file is None:
    print("Must supply input or file")
    sys.exit(-1)

parser = buildParser()

if args.input is not None:
    trees = list(parser.parse(args.input, trace=open('trace.dot','wt')))
if args.file is not None:
    trees = list(parser.parse(open(args.file).read(), trace=open('trace.dot','wt')))

if len(trees)==0:
    print("Parse error")
    sys.exit(-1)
if len(trees)>1:
    print(f"Warning: input is ambiguous, had {len(tree)} distinct parses")

result = Box.fromConstantExpression(trees[0])
pyResult = result.unbox()
if isinstance(pyResult,str):
    print(repr(pyResult))
else:
    print(pyResult)
