# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

def calcReachingDefs(entry):
    reaching = {}
    done = set()
    def process(block):
        for succ in (block.trueSucc,block.falseSucc):
            if succ is None:                          continue
            if not succ in reaching:                  reaching[succ] = {}
            for name, nameDef in block.defs.items():
                if name not in reaching[succ]:       reaching[succ][name] = set()
                reaching[succ][name].add((block,nameDef))
        done.add(block)
        if block.trueSucc is not None and block.trueSucc not in done:
            process(block.trueSucc)
        if block.falseSucc is not None and block.falseSucc not in done:
            process(block.falseSucc)
    process(entry)
    for blk,lookup in reaching.items():
        for name,defs in lookup.items():
            nameDefs = [ f'{srcBlock.label}/{val}' for (srcBlock,val) in defs ]
            print(f'{blk.label}: {name} = {",".join(nameDefs)}')
