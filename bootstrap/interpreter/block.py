# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .box import Box

class Instruction:
    def __init__(self, op, *values, function=None, name=None, theType=None, box=None, transfer=None):
        self.op = op
        self.values = values
        self.function = function
        self.name = name
        self.theType = theType
        self.box = box
        self.label = "unassigned"
        self.transfer = transfer

    def __str__(self):
        fields = []
        for attr in ('function','name','theType','box'):
            if getattr(self,attr) is not None:
                fields.append(f'{attr}={getattr(self,attr)}')
        if len(fields)>0:
            fieldStr = ' ' + ",".join(f for f in fields)
        else:
            fieldStr = ''
        return f'{self.op}({",".join(v.label for v in self.values)}{fieldStr})'

    @staticmethod
    def CALL(target, argument):
        return Instruction("call", argument, function=target)

    @staticmethod
    def CONSTANT(box):
        return Instruction("constant", box=box)

    @staticmethod
    def NEW(valType):
        return Instruction("new", theType=valType, transfer=lambda _:Box(valType))

    @staticmethod
    def RECORD_SET(record, name, value):
        return Instruction("record_set", record, value, name=name)

    @staticmethod
    def  SET_INSERT(theSet, newElement):
        return Instruction("set_insert", theSet, newElement)

class Block:
    counter = 1
    def __init__(self):
        self.instructions = []
        self.defs = {}
            # From symbol-table (i.e. first time use in this block no preceeding def)
            # From previous def
            # Constant
        self.uses = {}
        self.condition = None
        self.trueSucc  = None
        self.falseSucc = None
        self.preds     = set()
        self.label     = Block.counter
        Block.counter += 1

    def __str__(self):
        return f'bb({self.label},{len(self.instructions)})'

    def dump(self):
        self.makeLabels()
        print(f'{self}:')
        for i, inst in enumerate(self.instructions):
            print(f'  {self.label}_{i}: {inst}')

    def makeLabels(self):
        for i, inst in enumerate(self.instructions):
            inst.label = f'{self.label}_{i}'

    def addCondSucc(self, value, trueSucc, falseSucc):
        pass

    def addSucc(self, succ):
        pass



