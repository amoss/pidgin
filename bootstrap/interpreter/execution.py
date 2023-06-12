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

    def __init__(self, outermost, initialEnv, input=''):
        self.outermost = outermost
        main = outermost.children['main']
        mainEnv = main.typeEnv.makeCopy()
        mainEnv.add('stdin', Type.STRING())
        mainEnv.set('stdin', Box(Type.STRING(),raw=input))
        print('Setting up initial stack, main env:')
        mainEnv.dump()
        self.stack = [Execution.Frame(main, main.entry, 0, mainEnv)]
        outermost.entry.makeLabels()

    def step(self):
        if len(self.stack)==0:
            return False
        frame = self.stack[-1]
        if frame.position >= len(frame.current.instructions):
            if frame.current.trueSucc is None:
                if len(self.stack)==1:
                    frame.env.dump()
                    print('Done.')
                    return False
                result = frame.values[ frame.current.defs['%return%'] ]
                print(f'Returned len={len(self.stack)} with {result}')
                self.stack = self.stack[:-1]
                frame = self.stack[-1]
                inst = frame.current.instructions[frame.position]
                frame.values[inst] = result
                frame.position += 1
                return True
            if frame.current.falseSucc is None:
                frame.current = frame.current.trueSucc
                frame.position = 0
                return True
            conditional = frame.current.instructions[frame.position-1]
            print(f'Conditional jump {frame.values[conditional]} t={frame.current.trueSucc} f={frame.current.falseSucc}')
            assert frame.values[conditional].type.isBool(), f'Block conditional has wrong type'
            if frame.values[conditional].raw:
                frame.current = frame.current.trueSucc
            else:
                frame.current = frame.current.falseSucc
            frame.position = 0
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
            callEnv = function.typeEnv.makeCopy()
            args = frame.values[inst.values[0]]
            assert args.type.isRecord(), f'Cannot bind argument into child env, not record?'
            for k,v in args.raw.items():
                #callEnv.add(k,v.type)
                callEnv.set(k,v)
            self.stack.append( Execution.Frame(function, function.entry, 0, callEnv) )
            return True
        if inst.isLoad():
            frame.values[inst] = frame.env.values[inst.name]
            frame.position += 1
            return True
        if inst.isStore():
            frame.env.values[inst.name] = frame.values[inst.values[0]]
            print(f'Stored {frame.env.values[inst.name]} as {inst.name}')
            frame.env.dump()
            frame.position += 1
            return True
        assert False
        return False

