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

def findReachingDefs(name, block, memo):
    if block in memo.map:    return memo.map[block]
    merged = set()
    for pred in block.preds:
        merged.update( findDef(name, pred, memo) )     # All loops are broken by at least one def
    memo.update(block, merged)
    return merged

def findDef(name, block, memo):
    if block in memo.map:    return memo.map[block]
    lastDef = block.lastDefinition(name)
    if lastDef is not None:
        memo.store(block, (lastDef, block) )
        return memo.map[block]
    return findReachingDefs(name, block, memo)


def calcReachingDefs(func):
    funcArgs = func.type.param1.params
    memoTables = {}
    entry = func.entry
    for pair in funcArgs:
        print(f'Initial def of {pair[0]} in {func} is argument')
        memoTables[pair[0]] = MultiDict()
        memoTables[pair[0]].store( entry, (None,None) )

    for block in entry.reachable():
        for phi in block.instructions:
            if not phi.isPhi():     continue
            if phi.name not in memoTables:  memoTables[phi.name] = MultiDict()
            defs = findReachingDefs(phi.name, block, memoTables[phi.name])
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

