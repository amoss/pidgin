# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os, sys
thisDir = os.path.dirname(__file__)
rootDir = os.path.dirname(thisDir)
if rootDir not in sys.path:
    sys.path.append(rootDir)

import argparse
import importlib.util
import re
import shutil
import traceback

from bootstrap.grammar import Grammar
from bootstrap.machine import Automaton
from bootstrap.parser import Parser

GRAY = "\033[0;37m"
RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
END = "\033[0m"

# Convenience helpers, injected into tests namespace
def T(val, m=None, s=None):
    if m is None:
        if isinstance(val,str):
            return Grammar.TermString(val)
        return Grammar.TermSet(val)
    if isinstance(val,str):
        return Grammar.TermString(val, modifier=m)
    return Grammar.TermSet(val, modifier=m, strength=s)

def S(val, invert=False, m=None, s=None):
    if m is None:
        return Grammar.TermSet(val,inverse=invert)
    if s is None:
        return Grammar.TermSet(val,inverse=invert,modifier=m)
    return Grammar.TermSet(val,inverse=invert,modifier=m,strength=s)


def N(name, m='just', s='greedy'):
    return Grammar.Nonterminal(name, modifier=m, strength=s)

def Glue():
    return Grammar.Glue()

def Remove():
    return Grammar.Remover()

# Entry
argParser = argparse.ArgumentParser()
argParser.add_argument("-v","--verbose", action="store_true")
argParser.add_argument("-f","--filter")
argParser.add_argument("-p","--positive", type=int, default=-1)
argParser.add_argument("-n","--negative", type=int, default=-1)
argParser.add_argument("-s","--showtrees", action="store_true")
args = argParser.parse_args()
passed, failed = 0, 0
sys.setrecursionlimit(5000)

# Clean old results
target = os.path.join(rootDir, "results", "parser")
testBase = os.path.join(rootDir, "tests", "parser")
for name in os.listdir(target):
    if name==".keep" or name=="index.md" or name=='.DS_Store':  continue
    d = os.path.join(target,name)
    if args.verbose:                                            print(f"Cleaning {d}")
    shutil.rmtree(d)

# Scan units from files
units = []
largePositives = {}
injections = dict( (i.__qualname__,i) for i in (T,S,N,Glue,Remove,Grammar))
subDirs = [ os.path.join(testBase,e.name) for e in os.scandir(testBase) if e.is_dir() ]
for d in subDirs:
    files = [ e.name for e in os.scandir(os.path.join(testBase,d)) if e.name[-3:]=='.py' ]
    for f in files:
        spec = importlib.util.spec_from_file_location(f, os.path.join(d,f))
        module = importlib.util.module_from_spec(spec)
        for iname,i in injections.items():
            setattr(module, iname, i)
        try:
            spec.loader.exec_module(module)
            for name in dir(module):
                if name not in injections.keys() and name[:2]!='__':
                    entry = getattr(module,name)
                    if callable(entry):     # Filter out imports and data declarations
                        units.append((entry,os.path.basename(d) in ('units','toy')))
        except:
            print(f"{RED}Failed to load {d}/{f}{GRAY}")
            traceback.print_exc()
            print(END)
    caseSubdirs = [ os.path.join(d,e.name) for e in os.scandir(d) if e.is_dir() and e.name.startswith('positive_') ]
    for u in caseSubdirs:
        unitName = os.path.basename(u)[9:]
        for e in os.scandir(u):
            if e.name[0]=='.': continue
            if unitName not in largePositives:
                largePositives[unitName] = []
            largePositives[unitName].append(os.path.join(u,e.name))


def testPositive(parser, input, dir, name, caseName, snippet):
    global passed, failed
    results = [r for r in parser.execute(input, True)]
    parser.trace.output( open(os.path.join(dir,f'{caseName}.dot'),'wt') )
    if len(results)==0:
        print(f'{RED}Failed on {name} {caseName} {snippet}{END}')
        failed += 1
    else:
        passed += 1
        if args.verbose: print(f'{GREEN}Passed on {name} {caseName} {snippet}{END}')
        if args.showtrees:
            for j,r in enumerate(results):
                print(f'Result {j}')
                r.dump()
    redundant = parser.trace.measure()
    if redundant>0.5:
        print(f'{RED}High redundancy {redundant} on {name} {caseName} {snippet}{END}')
    if len(results)>1:
        print(f'{YELLOW}Ambiguous solutions on {name} {caseName} {snippet}{END}')

index = open( os.path.join(target,"index.md"), "wt")
for (u,addToDoc) in units:
    description   = u.__doc__
    lines         = description.split('\n')
    simple        = lines[0]
    justification = "\n".join(lines[2:])
    name          = u.__qualname__

    if addToDoc:
        print(f'\n## {name}', file=index)
        print(f'`{simple}`', file=index)
        print(justification, file=index)
        print(f'\n![eclr machine]({name}/eclr.dot.png)', file=index)

    if args.filter is not None and re.fullmatch(args.filter,name) is None: continue
    try:
        grammar, positive, negative, ambiguous = u()
        #grammar.dump()
        dir = os.path.join(target,name)
        os.makedirs(dir, exist_ok=True)
        automaton = Automaton(grammar)
        automaton.dot( open(os.path.join(dir,"eclr.dot"), "wt") )
        parser = Parser(automaton)

        for i,p in enumerate(positive):
            if args.negative!=-1: continue
            if args.positive!=-1 and i!=args.positive: continue
            if args.verbose: print(f'{GRAY}Executing p{i} on {name}: {p}{END}')
            testPositive(parser, p, dir, name, f'p{i}', p)

        if name in largePositives:
            for case in largePositives[name]:
                basename = os.path.basename(case)
                body = open(case,'rt').read()
                if args.verbose: print(f'{GRAY}Executing {basename} on {name}: {len(body)} cps{END}')
                testPositive(parser, body, dir, name, basename, f'{len(body)} cps')

        for i,n in enumerate(negative):
            if args.positive!=-1: continue
            if args.negative!=-1 and i!=args.negative: continue
            if args.verbose: print(f'{GRAY}Executing n{i} on {name}: {n}')
            results = [r for r in parser.execute(n, True)]
            parser.trace.output( open(os.path.join(dir,f'n{i}.dot'),'wt') )
            if len(results)>0:
                print(f'{RED}Failed on {name} negative {i} {n}{END}')
                failed += 1
                if args.showtrees:
                    for j,r in enumerate(results):
                        print(f'Result {j}')
                        r.dump()
            else:
                if args.verbose: print(f'{GREEN}Passed on {name} negative {i} {n}{END}')
                passed += 1

        for i,a in enumerate(ambiguous):
            if args.negative!=-1: continue
            if args.positive!=-1: continue
            if args.verbose: print(f'{GRAY}Executing a{i} on {name}: {a}')
            results = [r for r in parser.execute(a, True)]
            parser.trace.output( open(os.path.join(dir,f'a{i}.dot'),'wt') )
            if len(results)<2:
                print(f'{RED}Failed on {name} ambiguous {i} {a}{END}')
                failed += 1
            else:
                if args.verbose: print(f'{GREEN}Passed on {name} ambiguous {i} {a}{END}')
                passed += 1
                if args.showtrees:
                    for j,r in enumerate(results):
                        print(f'Result {j}')
                        r.dump()

    except:
        print(f"{RED}Failed to build case {u.__qualname__}{GRAY}")
        traceback.print_exc()
        print(END)
print(f'{passed} passed / {failed} failed')

