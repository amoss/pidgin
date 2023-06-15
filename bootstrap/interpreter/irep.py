# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .box import Box
from .types import Type

class Instruction:
    def __init__(self, op, *values, function=None, name=None, theType=None, box=None, transfer=None, position=None):
        self.op = op
        self.values = values
        self.function = function
        self.name = name
        self.theType = theType
        self.box = box
        self.label = "unassigned"
        self.position = position
        self.transfer = transfer

    def __str__(self):
        fields = []
        for attr in ('function','name','theType','box','position'):
            if getattr(self,attr) is not None:
                fields.append(f'{attr}={getattr(self,attr)}')
        if len(fields)>0:
            fieldStr = ' ' + ",".join(f for f in fields)
        else:
            fieldStr = ''
        return f'{self.op}({",".join(v.label for v in self.values)}{fieldStr})'

    def dot(self, output):
        if len(self.values)>0:
            cellLabel = self.op
            if self.name is not None:
                cellLabel += ' ' + self.name
            if self.function is not None:
                cellLabel += ' ' + self.function

            inPorts = [ f'<TD PORT="in{i}" HEIGHT="6" WIDTH="6" FIXEDSIZE="TRUE"><FONT POINT-SIZE="6">{i}</FONT></TD>'
                        for i in range(len(self.values)) ]
            inSpacing = [ '<TD></TD>' ] * len(inPorts)
            inCells = [cell for pair in zip(inPorts,inSpacing) for cell in pair][:-1]
            inRow = "".join(inCells)
            print(f' i{self.label} [shape=none,' +
                  f'label=<<TABLE BORDER="0" CELLBORDER="0" CELLPADDING="1"><TR>{inRow}</TR>' +
                  f'<TR><TD COLSPAN="{len(inCells)}">{cellLabel}</TD></TR>'
                  f'</TABLE>>];', file=output)
        else:
            print(f' i{self.label} [shape=none,label={self.op}];', file=output)

        for i,v in enumerate(self.values):
            print(f' i{v.label} -> i{self.label}:in{i};', file=output)

    def isCall(self):
        return self.op=="call"

    def isIterAccess(self):
        return self.op=="iter_access"

    def isLoad(self):
        return self.op=="load"

    def isStore(self):
        return self.op=="store"

    @staticmethod
    def ADD_NUMBER(lhs, rhs):
        return Instruction("add", lhs, rhs, transfer=lambda vs: Box(Type.NUMBER(), vs[0].raw + vs[1].raw))

    @staticmethod
    def CALL(target, argument):
        return Instruction("call", argument, function=target)

    @staticmethod
    def CONSTANT(box):
        return Instruction("constant", box=box, transfer=lambda _:box)

    @staticmethod
    def EQUAL(lhs, rhs):
        return Instruction("equal", lhs, rhs, transfer=lambda vs: Box(Type.BOOL(), vs[0].raw == vs[1].raw))

    @staticmethod
    def GREAT(lhs, rhs):
        return Instruction("great", lhs, rhs, transfer=lambda vs: Box(Type.BOOL(), vs[0].raw > vs[1].raw))

    @staticmethod
    def INEQUAL(lhs, rhs):
        return Instruction("inequal", lhs, rhs, transfer=lambda vs: Box(Type.BOOL(), vs[0].raw != vs[1].raw))

    @staticmethod
    def ITER_INIT(collection):
        return Instruction("iter_init", collection, transfer=lambda vs: Box(Type.ITERATOR(vs[0].type.param1),
                                                                            [0,len(vs[0].raw),tuple(vs[0].raw)]))
    # TODO: Iterator is a list as we have a dirty stateful hack to remove in execution.

    def ITER_CHECK(iterator):
        return Instruction("iter_check", iterator, transfer=lambda vs: Box(Type.BOOL(), vs[0].raw[0]<vs[0].raw[1]))

    def ITER_ACCESS(iterator):
        return Instruction("iter_access", iterator)

    @staticmethod
    def LESS(lhs, rhs):
        return Instruction("less", lhs, rhs, transfer=lambda vs: Box(Type.BOOL(), vs[0].raw < vs[1].raw))

    @staticmethod
    def LOAD(name):
        return Instruction("load", name=name)

    @staticmethod
    def NEW(valType):
        return Instruction("new", theType=valType, transfer=lambda _:Box(valType))

    @staticmethod
    def ORD_APPEND(ord, val):
        return Instruction("ord_append", ord, val, transfer=lambda vs: Box(vs[0].type, vs[0].raw + [val]))

    @staticmethod
    def RECORD_SET(record, name, value):
        return Instruction("record_set", record, value, name=name,
                           transfer=lambda vs: Box(vs[0].type, dict([(k,v) for k,v in vs[0].raw.items() if k!=name] + [(name,vs[1])])))

    @staticmethod
    def STORE(value, name):
        assert isinstance(name,str)
        return Instruction("store", value, name=name)

    @staticmethod
    def TUPLE_SET(record, pos, value):
        assert isinstance(pos,int)
        return Instruction("tuple_set", record, value, position=pos,
                           transfer=lambda vs: Box(vs[0].type, vs[0].raw[:pos]+(vs[1],)+vs[0].raw[pos+1:]))

    @staticmethod
    def  SET_INSERT(theSet, newElement):
        return Instruction("set_insert", theSet, newElement, transfer=lambda vs: Box(vs[0].type,vs[0].raw.union(set([vs[1]]))))

class Block:
    counter = 1
    def __init__(self):
        self.instructions = []
        self.defs = {}
        self.condition = None
        self.trueSucc  = None
        self.falseSucc = None
        self.preds     = set()
        self.label     = Block.counter
        Block.counter += 1

    def __str__(self):
        return f'bb({self.label},{len(self.instructions)})'

    def dump(self, done=None):
        if done is None:     done = set()
        print(f'{self}:')
        for i, inst in enumerate(self.instructions):
            print(f'  {self.label}_{i}: {inst}')
        if self.trueSucc is None:
            print(f'  Block exits function')
        else:
            print(f'  True  -> {self.trueSucc}')
        if self.falseSucc is not None:
            print(f'  False -> {self.falseSucc}')
        done.add(self)
        if self.trueSucc is not None and self.trueSucc not in done:
            self.trueSucc.dump(done=done)
        if self.falseSucc is not None and self.falseSucc not in done:
            self.falseSucc.dump(done=done)

    def dot(self, output):
        print('digraph {', file=output)
        print(f'subgraph bblock_{self.label} {{', file=output)
        for i in self.instructions:
            i.dot(output)
        print('}', file=output)
        print('}', file=output)

    def addCondSucc(self, value, trueSucc, falseSucc):
        pass

    def addSucc(self, succ):
        pass


class Function:
    def __init__(self, entry, typeEnv):
        self.children = {}
        self.typeEnv = typeEnv
        self.entry = entry
        self.name = None

    def dump(self):
        name = 'outermost' if self.name is None else self.name
        print(f'Function: {name}')
        self.typeEnv.dump()
        self.entry.dump()
        for c in self.children.values():
            c.dump()
        if '%return%' in self.entry.defs:
            print(f'return {self.entry.defs["%return%"]}')



