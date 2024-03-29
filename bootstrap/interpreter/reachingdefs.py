# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .irep import Value
from ..util import MultiDict

# Reaching definitions are used to calculate the placement of phi instructions. The standard
# approach is to calculate the dominance frontier and place nodes there in order to capture
# the joined flows. We use a simpler approach.

# A definition of a named variable can occur in three ways:
#   * A store instruction
#   * A phi instruction
#   * An original source (i.e. an argument)

# The initial estimation of phi-placement inserts a phi instruction in every block that uses
# a variable before definition within the block. Note, it does not matter if control flow
# joins at that block, before that block or not at all (w.r.t the name). This is an
# over-estimation, but it is locally decidable within each block and the presence of the
# redundant instructions simplifies the backwards search for inputs.

# The phi instructions inserted initially are empty, we want to update them in two ways:
#   * Insert the collection of values that flow into the instruction (tagged with the block
#     location of each input).
#   * Eliminate phi instructions with a single source.

# Because the search backwards for phi inputs is terminated by other phi instructions on the
# path - each solution is independent and static (w.r.t the program). This allows us to memoise
# the search results and so we only need to consider each block once. The result is (almost)
# linear (relying on the lookup speed in the memoisation dictionary).

# There might be a fast way to do the elimination as a DFS (because the sequence of rewrites is
# linear if we process the instructions in the right order and it is blocked by actual joins
# eliminating looping paths) ???

def findReachingDefs(name, block, memo, argNames):
    if len(block.preds)==0 and name in argNames:
        return set([(None,None)])
    merged = set()
    print(f'findReachingDef on blk{block.label} merging preds {[b.label for b in block.preds]}')
    for pred in block.preds:
        merged.update( findDef(name, pred, memo, argNames) )     # All loops are broken by at least one def
    return merged

def findDef(name, block, memo, argNames):
    if block in memo.map:    return memo.map[block]
    lastDef = block.lastDefinition(name)
    if lastDef is not None:
        print(f'findDef on blk{block.label} found last def {lastDef}')
        memo.store(block, (lastDef, block) )
        return memo.map[block]
    print(f'blk{block.label} had no lastDef for {name} - searching')
    incoming = findReachingDefs(name, block, memo, argNames)
    memo.update(block, incoming)
    return incoming


def calcReachingDefs(func):
    funcArgs = func.type.param1.params
    memoTables = {}
    entry = func.entry
    argNames = [pair[0] for pair in funcArgs]

    func.dump()

    for block in entry.reachable():
        for phi in block.instructions:
            if not phi.isPhi() or len(phi.values)>0:     continue
            if phi.name not in memoTables:  memoTables[phi.name] = MultiDict()
            defs = findReachingDefs(phi.name, block, memoTables[phi.name], argNames)
            print(f'In blk{block.label}: {phi} updating with {defs}')
            sources, phi.inputBlocks = zip(*defs)
            values = []
            for s in sources:
                if s is None:
                    values.append(Value(argument=phi.name))
                else:
                    values.append(Value(instruction=s))
            phi.values = values
    for name,memo in memoTables.items():
        print(f'Final memo: {name} <- {memo}')

