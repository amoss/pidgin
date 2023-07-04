# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

def eliminatePhi(func):
    for block in func.entry.reachable():
        delete = []
        for inst in block.instructions:
            if not inst.isPhi():    continue
            if inst in inst.uses:
                print(f'Eliminate self-loop on phi {inst}')
                inst.uses = [ u for u in inst.uses if u != inst ]
                inst.values = tuple(v for v in inst.values if v.instruction!=inst)
            if len(inst.values)==1:
                print(f'Eliminate redundant phi {inst}')
                for eachUse in inst.uses:
                    eachUse.replace(inst, inst.values[0])
                delete.append(inst)
        if len(delete)>0:
            block.instructions = [ inst for inst in block.instructions if inst not in delete ]



