# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os, sys
thisDir = os.path.dirname(__file__)
rootDir = os.path.dirname(thisDir)
if rootDir not in sys.path:
    sys.path.append(rootDir)

import argparse
import re

from bootstrap.interpreter import buildPidginParser, Box
from bootstrap.util import dump

GRAY = "\033[0;37m"
RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
END = "\033[0m"

# Entry
argParser = argparse.ArgumentParser()
argParser.add_argument("-v","--verbose", action="store_true")
argParser.add_argument("-f","--filter")
argParser.add_argument("-t","--parsetrees", action="store_true")
argParser.add_argument("-s","--start", default="expr")
argParser.add_argument("-p","--parsetraces", action="store_true")
args = argParser.parse_args()
passed, failed = 0, 0
sys.setrecursionlimit(5000)

def collect(dir):
    results, subDirs = set(), set()
    for e in os.scandir(dir):
        if e.is_dir():
            subDirs.append(os.path.join(dir,e.name))
        else:
            if e.name.endswith('.pidg'):
                results.add(os.path.join(dir,e.name))
    for sub in subDirs:
        results.update(collect(dir))
    return results

parser = buildPidginParser(start=args.start)

for filename in collect(thisDir):
    if args.filter is not None and re.fullmatch(args.filter,filename) is None:  continue
    cases = open(filename).read().split('\n')
    for i,case in enumerate(cases):
        if len(case)==0:  continue
        input, output = case.split(' | ')
        if args.verbose: print(f'{GRAY}Testing {filename} {i}: {input}{END}')
        try:
            trees = [r for r in parser.execute(input, args.parsetraces)]
        except:
            trees = []
        if args.parsetraces:
            parser.trace.output( open(os.path.join(rootDir,'results',f'{filename}{i}.dot'),'wt') )
        if len(trees)==0:
            print(f'{RED}Failed to parse {filename} {i}: {input}{END}')
        else:
            if len(trees)>1:
                print(f'{YELLOW}Ambiguous parse for {filename} {i}')
            if args.parsetrees:
                dump(trees[0])
            result = Box.fromConstantExpression(trees[0])
            pyResult = result.unbox()
            if isinstance(pyResult,str):
                strResult = repr(pyResult)
            else:
                strResult = str(pyResult)
            if strResult!=output:
                print(f'{RED}{filename} {i}, output is wrong, expected: {pyResult}')
                print(f'  actual: {strResult}{END}')
            elif args.verbose:
                print(f'{GREEN}Passed on {filename} {i}: {input}{END}')
