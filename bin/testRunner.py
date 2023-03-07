# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os, sys
rootDir= os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

import argparse
import ctypes
import importlib.util
import itertools
import shutil
import sys
import threading
import traceback

from bootstrap.generator import Generator
from bootstrap.parser import Parser
import bootstrap.selfhost as selfhost

GRAY = "\033[0;37m"
RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
END = "\033[0m"

class Timeout(Exception):
    pass

def generateWhileProductive(grammar, targetPath, numSentences=20):
    generator = Generator(grammar)
    succeeded = True
    with open(os.path.join(target, "gentrace.dot"),"wt") as traceFile:
        iterator = generator.step(trace=traceFile)
        def emitOne():
            try:
                sentences.append(next(iterator))
            except StopIteration:
                pass
        for i in range(numSentences):
            thread = threading.Thread(target=emitOne)
            thread.start()
            thread.join(timeout=2)
            if thread.is_alive():
                succeeded = False
                exception = ctypes.py_object(Timeout)
                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), exception)
                thread.join()
                break
        print("}", file=traceFile)
    with open(os.path.join(target, "generated.txt"),"wt") as outputFile:
        for s in sentences:
            s = [ symb.string if symb.string is not None else str(symb) for symb in s]
            outputFile.write(" ".join(s))
            outputFile.write("\n")
    return succeeded

def parseQuickly(parser, line, trace=None):
    result = []
    def wrapParse():
        result.extend(list(parser.parse(line,trace=trace)))
    thread = threading.Thread(target=wrapParse)
    thread.start()
    thread.join(timeout=2)
    if thread.is_alive():
        exception = ctypes.py_object(Timeout)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), exception)
        thread.join()
    return result

def testcases(dir, filename):
    try:
        testFile = open(os.path.join(dir,filename))
    except:
        return
    for line in testFile.readlines():
       yield line.rstrip("\n")

def testPositives(dir, parser):
    global args
    traceCounter = 1
    for line in testcases(dir, "positive.txt"):
        if args.traces:
            trace = open(os.path.join(target,f"failure{traceCounter}.dot"),"wt")
        else:
            trace = None
        results = parseQuickly(parser,line,trace=trace)
        if len(results)==1:
            if args.verbose:
                print(f"{GREEN}Parsed positive example {line}{END}")
        elif len(results)>1:
            print(f"{YELLOW}Ambiguous result for positive {line}{END}")
        else:
            traceCounter += 1
            print(f"{RED}Failed to parse positive example {line}{END}")

def testNegatives(dir, parser):
    global args
    traceCounter = 1
    for line in testcases(dir, "negative.txt"):
        if args.traces:
            trace = open(os.path.join(target,f"failure{traceCounter}.dot"),"wt")
        else:
            trace = None
        results = parseQuickly(parser,line,trace=trace)
        if len(results)==0:
            if args.verbose:
                print(f"{GREEN}Failed to parse negative example {line}{END}")
        else:
            traceCounter += 1
            print(f"{RED}Parsed negative example {line}{END}")

def testAmbiguities(dir, parser):
    global args
    traceCounter = 1
    for line in testcases(dir, "ambiguous.txt"):
        if args.traces:
            trace = open(os.path.join(target,f"failure{traceCounter}.dot"),"wt")
        else:
            trace = None
        results = parseQuickly(parser,line,trace=trace)
        if len(results)>1:
            if args.verbose:
                print(f"{GREEN}Parsed ambiguous example {line}{END}")
        elif len(results)==1:
            print(f"{YELLOW}Single result for ambiguous {line}{END}")
        else:
            traceCounter += 1
            print(f"{RED}Failed to parse ambiguous example {line}{END}") 

argParser = argparse.ArgumentParser()
argParser.add_argument("-v","--verbose", action="store_true")
argParser.add_argument("-f","--filter")
argParser.add_argument("-t","--traces", action="store_true")
args = argParser.parse_args()

# Clean old results
target = os.path.join(rootDir,"results")
for name in os.listdir(target):
    if name==".keep":  continue
    dir = os.path.join(target,name)
    print(f"Cleaning {dir}")
    shutil.rmtree(dir)

# Generate new result set
stage1g = selfhost.stage1()
stage1 = Parser(stage1g, stage1g.discard)
for name in sorted(os.listdir( os.path.join(rootDir,"tests") )):
    if args.filter is not None and args.filter not in name: continue
    dir = os.path.join(rootDir,"tests",name)
    spec = importlib.util.spec_from_file_location(name, os.path.join(dir,"bootstrapper.py"))
    module = importlib.util.module_from_spec(spec)
    target = os.path.join(rootDir,"results",name)
    os.makedirs(target, exist_ok=True)
    try:
        spec.loader.exec_module(module)
        print(f"Loaded {name}")
        grammar = module.build()
        print(f"{GREEN}Initialized {name}{END}")
        sentences = []
        if generateWhileProductive(grammar, target):
            if args.verbose:
                print(f"{GREEN}Generated from {name}{END}")
        else:
            print(f"{RED}Failed to generate from {name}{END}")

        traceCounter = 1
        parser = Parser(grammar, discard=grammar.discard)
        parser.dotAutomaton(open(os.path.join(target, "lr0.dot"),"wt"))
        testPositives(dir, parser)
        testNegatives(dir, parser)
        testAmbiguities(dir, parser)
    except FileNotFoundError:
        pass
    except:
        print(f"{RED}Failed on {name}{GRAY}")
        traceback.print_exc()
        print(END)

    try:
        res = list(stage1.parse( open(os.path.join(dir,"grammar.g")).read(), transformer=selfhost.transformer))
        if len(res)==1:
            print(f"{GREEN}Initialized grammar {name}{END}")
        elif len(res)>1:
            print(f"{RED}Grammar {name} was ambiguous{END}")
            continue
        else:
            print(f"{RED}Grammar {name} failed to parse{END}")
            continue
        stage2g = selfhost.stage2(res[0])
        parser2 = Parser(stage2g, discard=stage2g.Terminal(set(" \t\r\n"), "some"))
        testPositives(dir, parser2)
        testNegatives(dir, parser2)
        testAmbiguities(dir, parser2)

    except FileNotFoundError:
        pass
    except:
        print(f"{RED}Failed on grammar {name}{GRAY}")
        traceback.print_exc()
        print(END)


print("Done.")
