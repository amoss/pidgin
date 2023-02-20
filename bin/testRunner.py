import os, sys
rootDir= os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

import importlib.util
import itertools
import shutil
import sys
import traceback

from bootstrap.generator2 import Generator

GRAY = "\033[0;37m"
RED = "\033[1;31m"
GREEN = "\033[1;32m"
END = "\033[0m"

# Clean old results
target = os.path.join(rootDir,"results")
for name in os.listdir(target):
    if name==".keep":  continue
    dir = os.path.join(target,name)
    print(f"Cleaning {dir}")
    shutil.rmtree(dir)

for name in sorted(os.listdir( os.path.join(rootDir,"tests") )):
    dir = os.path.join(rootDir,"tests",name)
    spec = importlib.util.spec_from_file_location(name, os.path.join(dir,"bootstrapper.py"))
    module = importlib.util.module_from_spec(spec)
    target = os.path.join(rootDir,"results",name)
    os.makedirs(target, exist_ok=True)
    try:
        spec.loader.exec_module(module)
        print(f"Loaded {name}")
        grammar, graph = module.build()
        print(f"{GREEN}Executed {name}{END}")
        graph.dot(open(os.path.join(target, "tree.dot"),"wt"))
        generator = Generator(grammar)
        with open(os.path.join(target, "gentrace.dot"),"wt") as traceFile:
            sentences = list(itertools.islice(generator.step(trace=traceFile), 20))
        with open(os.path.join(target, "generated.txt"),"wt") as outputFile:
            for s in sentences:
                s = [ symb.string if symb.string is not None else symb for symb in s]
                outputFile.write(" ".join(s))
                outputFile.write("\n")
    except:
        print(f"{RED}Failed on {name}{GRAY}")
        traceback.print_exc()
        print(END)

print("Done.")
