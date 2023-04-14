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

#from bootstrap.grammar import Grammar
import monster
Grammar = monster.Grammar

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


def N(name, modifier='just', strength='greedy'):
    return Grammar.Nonterminal(name, modifier=modifier, strength=strength)


# Entry
argParser = argparse.ArgumentParser()
argParser.add_argument("-v","--verbose", action="store_true")
argParser.add_argument("-f","--filter")
args = argParser.parse_args()

# Clean old results
target = os.path.join(rootDir,"unitResults")
for name in os.listdir(target):
    if name==".keep" or name=="index.md" or name=='.DS_Store':  continue
    d = os.path.join(target,name)
    print(f"Cleaning {d}")
    shutil.rmtree(d)

# Scan units from files
units = []
injections = dict( (i.__qualname__,i) for i in (T,S,N,Grammar))
subDirs = [ os.path.join(thisDir,e.name) for e in os.scandir(thisDir) if e.is_dir() ]
for d in subDirs:
    files = [ e.name for e in os.scandir(d) if e.name[-3:]=='.py' ]
    for f in files:
        spec = importlib.util.spec_from_file_location(f, os.path.join(d,f))
        module = importlib.util.module_from_spec(spec)
        for iname,i in injections.items():
            setattr(module, iname, i)
        try:
            spec.loader.exec_module(module)
            for name in dir(module):
                if name not in injections.keys() and name[:2]!='__':
                    units.append((getattr(module,name),d=='units'))
        except:
            print(f"{RED}Failed to load {d}/{f}{GRAY}")
            traceback.print_exc()
            print(END)


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
        grammar, positive, negative = u()
        #grammar.dump()
        dir = os.path.join(target,name)
        os.makedirs(dir, exist_ok=True)
        automaton = monster.Automaton(grammar)
        automaton.dot( open(os.path.join(dir,"eclr.dot"), "wt") )

        for i,p in enumerate(positive):
            if args.verbose: print(f'{GRAY}Executing p{i} on {name}: {p}')
            results = [r for r in automaton.execute(p, True)]
            automaton.trace.output( open(os.path.join(dir,f'p{i}.dot'),'wt') )
            if len(results)==0:
                print(f'{RED}Failed on {name} positive {i} {p}{END}')
            elif args.verbose:
                print(f'{GREEN}Passed on {name} positive {i} {p}{END}')
        for i,n in enumerate(negative):
            if args.verbose: print(f'{GRAY}Executing n{i} on {name}: {n}')
            results = [r for r in automaton.execute(n, True)]
            automaton.trace.output( open(os.path.join(dir,f'n{i}.dot'),'wt') )
            if len(results)>0:
                print(f'{RED}Failed on {name} negative {i} {n}{END}')
            elif args.verbose:
                print(f'{GREEN}Passed on {name} negative {i} {n}{END}')
    except:
        print(f"{RED}Failed to build case {u.__qualname__}{GRAY}")
        traceback.print_exc()
        print(END)

