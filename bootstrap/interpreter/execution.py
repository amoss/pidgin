# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from dataclasses import dataclass, field

from .irep import Block, Instruction, Function
from .box import Box, Type
from .frontend import AST
from .typecheck import TypedEnvironment
from ..parser import Token
from ..util import dump


class Execution:
    @dataclass
    class Frame:
        function: Function
        current: Block
        position: int
        env: TypedEnvironment
        values: dict[Instruction,Box] = field(default_factory=dict)

    def __init__(self, outermost, initialEnv):
        self.outermost = outermost
        self.stack = [Execution.Frame(outermost, outermost.entry, 0, initialEnv)]
        outermost.entry.makeLabels()

    def step(self):
        if len(self.stack)==0:
            return False
        frame = self.stack[-1]
        if frame.position >= len(frame.current.instructions):
            if len(self.stack)==1  and  not '%return%' in frame.current.defs:
                frame.env.dump()
                print('Done.')
                return False
            result = frame.values[ frame.current.defs['%return%'] ]
            self.stack = self.stack[:-1]
            frame = self.stack[-1]
            inst = frame.current.instructions[frame.position]
            frame.values[inst] = result
            frame.position += 1
            return True
        inst = frame.current.instructions[frame.position]
        print(f'step {frame.current.label}_{frame.position}: {inst}')
        if hasattr(inst, 'transfer')  and  getattr(inst, 'transfer') is not None:
            inputs = []
            for v in inst.values:
                assert v in frame.values, f'Instruction {inst} requires unevaluated value {v}'
                inputs.append(frame.values[v])
            result = inst.transfer(tuple(inputs))
            frame.values[inst] = result
            frame.position += 1
            return True
        if inst.isCall():
            fType = frame.env.types[inst.function]
            if fType.isBuiltin():
                print(f'calling builtin {inst.function} env: {",".join(frame.env.values.keys())}')
                arg = frame.values[inst.values[0]]
                result = fType.builtin(arg)
                frame.values[inst] = result
                frame.position += 1
                return True
            function = fType.function
            childEnv = frame.env.makeChild()
            args = frame.values[inst.values[0]]
            assert args.type.isRecord(), f'Cannot bind argument into child env, not record?'
            for k,v in args.raw.items():
                childEnv.add(k,v.type)
                childEnv.set(k,v)
            self.stack.append( Execution.Frame(function, function.entry, 0, childEnv) )
            return True
        if inst.isLoad():
            frame.values[inst] = frame.env.values[inst.name]
            frame.position += 1
            return True
        if inst.isStore():
            frame.env.values[inst.name] = frame.values[inst.values[0]]
            frame.position += 1
            return True
        assert False
        return False

