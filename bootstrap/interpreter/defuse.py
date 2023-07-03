# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.


def calcDefUse(func):
    for block in func.entry.reachable():
        for inst in block.instructions:
            inst.uses = set()
    for block in func.entry.reachable():
        for inst in block.instructions:
            for value in inst.values:
                if value.instruction is not None:
                    value.instruction.uses.add(inst)
