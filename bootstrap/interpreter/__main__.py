# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

import argparse
import traceback

from bootstrap.interpreter import buildPidginParser, Box, execute, Environment, Type, TypeEnvironment, TypingFailed
import bootstrap.interpreter.builtins as builtins
from bootstrap.util import dump


argParser = argparse.ArgumentParser()
argParser.add_argument("-i", "--input")
argParser.add_argument("-f", "--file")
argParser.add_argument("-s", "--start", default="expr")
argParser.add_argument("-d", "--dumpast", action="store_true")
args = argParser.parse_args()

if args.input is None and args.file is None:
    print("Must supply input or file")
    sys.exit(-1)

sys.setrecursionlimit(5000)
parser = buildPidginParser(start=args.start)

if args.input is not None:
    trees = list(parser.execute(args.input, True))
    parser.trace.output(open('inttrace.dot','wt'))
if args.file is not None:
    trees = list(parser.execute(open(args.file).read(), True))
    parser.trace.output(open('inttrace.dot','wt'))

if len(trees)==0:
    print("Parse error")
    sys.exit(-1)
if len(trees)>1:
    print(f"Warning: input is ambiguous, had {len(trees)} distinct parses")
    for i,t in enumerate(trees):
        print(f'Parse tree {i}')
        dump(t)

if args.dumpast:
    dump(trees[0])

if args.start=='expr':
    typeEnv = TypeEnvironment()
    typeEnv.fromExpression(trees[0])
    result = Box.fromConstantExpression(trees[0])
    pyResult = result.unbox()
    if isinstance(pyResult,str):
        print(repr(pyResult))
    else:
        print(pyResult)
elif args.start=='program':
    try:
        typeEnv = TypeEnvironment()
        typeEnv.fromScope(trees[0])
    except TypingFailed as e:
        traceback.print_exc()
        dump(e.tree)
        sys.exit(-1)
    env = Environment()
    env.insert('len', Type('builtin'), builtins.builtin_len)
    execute(trees[0], env)
    env.dump()
else:
    assert False, "Unexpected entry point {args.start}"
