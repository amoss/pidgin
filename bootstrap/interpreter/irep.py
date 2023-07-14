# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .box import Box
from .types import Type

class Instruction:
    def __init__(self, op, *values, function=None, name=None, theType=None, outTypes=None, box=None, transfer=None,
                 position=None):
        self.op = op
        self.values = values
        for v in values:
            assert isinstance(v, Value), v
        self.function = function
        self.name = name
        self.theType = theType
        self.outTypes = outTypes
        self.box = box
        self.label = "unassigned"
        self.position = position
        self.transfer = transfer
        self.block = None

    def __str__(self):
        fields = []
        for attr in ('function','name','theType','box','position'):
            if getattr(self,attr) is not None:
                fields.append(f'{attr}={getattr(self,attr)}')
        if hasattr(self,'uses'):
            fields.append(f'uses={len(getattr(self,"uses"))}')
        if len(fields)>0:
            fieldStr = ' ' + ",".join(f for f in fields)
        else:
            fieldStr = ''
        return f'{self.op}({",".join(str(v) for v in self.values)}{fieldStr})'

    def dotNode(self, blockName, output):
        cellLabel = self.op
        if self.name is not None:
            cellLabel += ' ' + self.name
        if self.function is not None:
            cellLabel += ' ' + self.function
#        if len(self.values)>0:
#            inPorts = [ f'<TD PORT="in{i}" HEIGHT="6" WIDTH="6" FIXEDSIZE="TRUE"><FONT POINT-SIZE="6">{i}</FONT></TD>'
#                        for i in range(len(self.values)) ]
#            inSpacing = [ '<TD></TD>' ] * len(inPorts)
#            inCells = [cell for pair in zip(inPorts,inSpacing) for cell in pair][:-1]
#            inRow = "".join(inCells)
#            print(f' i{self.label} [shape=none,' +
#                  f'label=<<TABLE BORDER="0" CELLBORDER="0" CELLPADDING="1"><TR>{inRow}</TR>' +
#                  f'<TR><TD COLSPAN="{len(inCells)}">{cellLabel}</TD></TR>' +
#                  outRow +
#                  f'</TABLE>>];', file=output)
#        else:
#            print(f' i{self.label} [shape=none,label="{cellLabel}"];', file=output)

        inRow, outRow, width = '', '', 1
        if len(self.values)>0:
            inPorts = [ f'<TD PORT="in{i}" HEIGHT="6" WIDTH="6" FIXEDSIZE="TRUE"><FONT POINT-SIZE="6">{i}</FONT></TD>'
                        for i in range(len(self.values)) ]
            inSpacing = [ '<TD></TD>' ] * len(inPorts)
            inCells = [cell for pair in zip(inPorts,inSpacing) for cell in pair][:-1]
            if len(inCells)>width:
                width = len(inCells)
            inRow = '<TR>' + "".join(inCells) + '</TR>'
        if self.outTypes is not None and self.theType is None:
            outPorts = [ f'<TD PORT="out{i}" HEIGHT="6" WIDTH="6" FIXEDSIZE="TRUE"><FONT POINT-SIZE="6">{i}</FONT></TD>'
                        for i in range(len(self.outTypes)) ]
            outSpacing = [ '<TD></TD>' ] * len(outPorts)
            outCells = [cell for pair in zip(outPorts,outSpacing) for cell in pair][:-1]
            if len(outCells)>width:
                width = len(outCells)
            outRow = '<TR>' + "".join(outCells) + '</TR>'
        print(f' i{self.label} [shape=none,label=<<TABLE BORDER="0" CELLBORDER="0" CELLPADDING="1">' +
              inRow +
              f'<TR><TD COLSPAN="{width}">{cellLabel}</TD></TR>' +
              outRow +
              '</TABLE>>];', file=output)


    def dotEdges(self, blockName, output):
        if len(self.values)==0:
            print(f' {blockName}_entry -> i{self.label} [color=none];', file=output)

        for i,v in enumerate(self.values):
            if v.constant is not None:
                print(f'v{hash(v)} [label="{str(v.constant)}"];', file=output)
                print(f'v{hash(v)} -> i{self.label}:in{i};', file=output)
            if v.instruction is not None:
                print(f' i{v.instruction.label} -> i{self.label}:in{i};', file=output)
            if v.argument is not None:
                print(f' arg_{v.argument} -> i{self.label}:in{i};', file=output)

    def isCall(self):
        return self.op=="call"

    def isIterAccess(self):
        return self.op=="iter_access"

    def isLoad(self):
        return self.op=="load"

    def isPhi(self):
        return self.op=="phi"

    def isStore(self):
        return self.op=="store"

    def replace(self, value, replacement):
        newValues = list(self.values)
        if isinstance(value, Instruction):
            for i in range(len(self.values)):
                if self.values[i].instruction==value:
                    newValues[i] = replacement
            self.values = newValues
        else:
            assert False

    @staticmethod
    def ADD_NUMBER(lhs, rhs):
        t = Type.NUMBER()
        return Instruction("add", lhs, rhs, theType=t, transfer=lambda vs: Box(t, vs[0].raw + vs[1].raw))

    @staticmethod
    def CALL(target, retType, argument):
        return Instruction("call", argument, function=target, theType=retType)

    @staticmethod
    def EQUAL(lhs, rhs):
        t = Type.BOOL()
        return Instruction("equal", lhs, rhs, theType=t, transfer=lambda vs: Box(t, vs[0].raw == vs[1].raw))

    @staticmethod
    def GREAT(lhs, rhs):
        t = Type.BOOL()
        return Instruction("great", lhs, rhs, theType=t, transfer=lambda vs: Box(t, vs[0].raw > vs[1].raw))

    @staticmethod
    def INEQUAL(lhs, rhs):
        t = Type.BOOL()
        return Instruction("inequal", lhs, rhs, theType=t, transfer=lambda vs: Box(t, vs[0].raw != vs[1].raw))

    @staticmethod
    def ITER_INIT(collection):
        print(f'Init iterator from {type(collection)} {collection.type()}')
        itType = Type.ITERATOR(collection.type().param1)      # NOTE: Will be different for maps
        return Instruction("iter_init", collection, theType=itType,
                           transfer=lambda vs: Box(itType, (0,len(vs[0].raw),tuple(vs[0].raw))))

    def ITER_CHECK(iterator):
        t = Type.BOOL()
        return Instruction("iter_check", iterator, theType=t, transfer=lambda vs: Box(t, vs[0].raw[0]<vs[0].raw[1]))

    def ITER_ACCESS(iterator):
        '''Output 0 is the new iterator state
           Output 1 is the iterated value.'''
        t = iterator.type()
        return Instruction("iter_access", iterator, outTypes=(t,t.param1),
                           transfer=lambda vs: (Box(t, (vs[0].raw[0]+1, vs[0].raw[1], vs[0].raw[2])),
                                                # Box(t.param1, vs[0].raw[2][vs[0].raw[0].raw]) ) boxes are immutable
                                                vs[0].raw[2][vs[0].raw[0]] )
                          )

    @staticmethod
    def LESS(lhs, rhs):
        t = Type.BOOL()
        return Instruction("less", lhs, rhs, theType=t, transfer=lambda vs: Box(t, vs[0].raw < vs[1].raw))

    @staticmethod
    def LOAD(name):
        return Instruction("load", name=name)

    @staticmethod
    def NEW(valType):
        return Instruction("new", theType=valType, transfer=lambda _:Box(valType))

    @staticmethod
    def ORD_APPEND(ord, val):
        t = ord.type()
        return Instruction("ord_append", ord, val, theType=t, transfer=lambda vs: Box(t, vs[0].raw + [val]))

    @staticmethod
    def PHI(name, theType):
        return Instruction("phi", name=name, theType=theType)

    @staticmethod
    def RECORD_SET(record, name, value):
        t = record.type()
        return Instruction("record_set", record, value, name=name, theType=t,
                           transfer=lambda vs: Box(t, dict([(k,v) for k,v in vs[0].raw.items() if k!=name] + [(name,vs[1])])))

    @staticmethod
    def SET_INSERT(theSet, newElement):
        t = theSet.type()
        return Instruction("set_insert", theSet, newElement, theType=t,
                           transfer=lambda vs: Box(t, vs[0].raw.union(set([vs[1]]))))

    @staticmethod
    def STORE(value, name):
        assert isinstance(name,str)
        return Instruction("store", value, name=name, theType=value.type())

    @staticmethod
    def TUPLE_SET(record, pos, value):
        assert isinstance(pos,int)
        t = record.type()
        return Instruction("tuple_set", record, value, position=pos, theType=t,
                           transfer=lambda vs: Box(t, vs[0].raw[:pos]+(vs[1],)+vs[0].raw[pos+1:]))


class Value:
    def __init__(self, instruction=None, output=None, argument=None, constant=None):
        self.instruction = instruction
        assert instruction is None  or  isinstance(instruction,Instruction), instruction
        self.output = output
        assert output is None  or  instruction is not None, f'Output index needs an instruction source'
        self.argument = argument
        self.constant = constant
        assert constant is None  or  isinstance(constant,Box), constant
        assert len([x for x in (instruction,argument,constant) if x is not None])==1

    def __str__(self):
        if self.instruction is not None:
            if self.output is None:
                return f'i{self.instruction.label}'
            return f'i{self.instruction.label}#{self.output}'
        if self.constant is not None:
            return f'constant {self.constant}'
        if self.argument is not None:
            return f'arg={self.argument}'
        assert False

    def sig(self):
        return (self.instruction, self.output, self.argument, self.constant)

    def __hash__(self):
        return hash(self.sig())

    def __eq__(self, other):
        return self.sig()==other.sig()

    def type(self):
        if self.instruction is not None and self.output is None:
            assert self.instruction.theType is not None, self.instruction
            return self.instruction.theType
        if self.instruction is not None and self.output is not None:
            return self.instruction.outTypes[self.output]
        if self.constant is not None:
            return self.constant.type
        assert False


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


    def connect(self, condition, succ):
        if condition:
            self.trueSucc = succ
        else:
            self.falseSucc = succ
        succ.preds.add(self)


    def dotDecls(self, output):
        print(f'subgraph cluster_bblock{self.label} {{', file=output)
        print(' color=grey;', file=output)
        print(f' bblock{self.label}_entry [shape=none, fontcolor="grey"];', file=output)
        print(f' bblock{self.label}_exit [shape=none, fontcolor="grey"];', file=output)
        for i in self.instructions:
            i.dotNode(f'bblock{self.label}',output)
        print('}', file=output)


    def dotEdges(self, output):
        for i in self.instructions:
            i.dotEdges(f'bblock{self.label}',output)
        if len(self.instructions)>0:
            print(f' i{self.instructions[-1].label} -> bblock{self.label}_exit [color=none];', file=output)


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
        for k,v in self.defs.items():
            print(f'  def {k} <- {v}')
        done.add(self)
        if self.trueSucc is not None and self.trueSucc not in done:
            self.trueSucc.dump(done=done)
        if self.falseSucc is not None and self.falseSucc not in done:
            self.falseSucc.dump(done=done)


    def insert(self, instruction, pos=-1):
        instruction.block = self
        if pos==-1:
            instruction.label = f'{self.label}_{len(self.instructions)}'
            self.instructions.append(instruction)
        else:
            self.instructions = self.instructions[:pos] + [instruction] + self.instructions[pos:]
            for i in range(pos, len(self.instructions)+1):
                self.instructions[i].label = f'{self.label}_{i}'
        return instruction

    def lastDefinition(self, name):
        result = None
        for i in self.instructions:
            if (i.isStore() or i.isPhi()) and i.name==name:
                result = i
        return result


    def reachable(self, done=None):
        if done is None:     done = set()
        if self in done:     return
        yield self
        done.add(self)
        if self.trueSucc is not None  and  not self.trueSucc in done:
            for block in self.trueSucc.reachable(done=done):
                yield block
        if self.falseSucc is not None  and  not self.falseSucc in done:
            for block in self.falseSucc.reachable(done=done):
                yield block


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

    def dot(self, output):
        print('digraph {', file=output)
        for block in self.entry.reachable():
            block.dotDecls(output)
            if block.trueSucc is not None:
                print(f' bblock{block.label}_exit -> bblock{block.trueSucc.label}_entry '
                       '[label="true",color="grey",fontcolor="grey"];', file=output)
            if block.falseSucc is not None:
                print(f' bblock{block.label}_exit -> bblock{block.falseSucc.label}_entry ' +
                       '[label="false",color="grey",fontcolor="grey"];', file=output)
        for block in self.entry.reachable():
            block.dotEdges(output)

        print('}', file=output)


