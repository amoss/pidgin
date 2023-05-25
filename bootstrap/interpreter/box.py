# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .frontend import AST
from .types import Type
from ..parser import Parser, Token
from ..util import dump

class Box:
    def __init__(self, type, raw):
        self.type = type
        self.raw = raw

    def __eq__(self, other):
        return isinstance(other,Box) and self.type==other.type and self.raw==other.raw

    def __hash__(self):
        return hash((self.type,self.raw))

    def __str__(self):
        return f'box({self.type},{self.raw})'

    def plusTypeCheck(left, right):
        if not left.eqOrCoerce(right): return None
        if left.label=='{}':
            return lambda l,r: Box(l.type.join(r.type),l.raw | r.raw)
        return lambda l,r: Box(l.type.join(r.type),l.raw+r.raw)

    def postfixTypeCheck(left, right):
        if not left.eqOrCoerce(right): return None
        if (left.label=='[]' and right.label=='[]') or \
           (left.label=='S'  and right.label=='S'):
            return lambda l,r: Box(l.type.join(r.type), l.raw+r.raw)

    def prefixTypeCheck(left, right):
        if not left.eqOrCoerce(right): return None
        if (left.label=='[]' and right.label=='[]') or \
           (left.label=='S'  and right.label=='S'):
            return lambda l,r: Box(l.type.join(r.type), r.raw+l.raw)

    def subTypeCheck(left, right):
        if not left.eqOrCoerce(right): return None
        if left.label=='{}':
            return lambda l,r: Box(l.type.join(r.type),l.raw.difference(r.raw))
        if left.label=='N':
            return lambda l,r: Box(l.type.join(r.type),l.raw-r.raw)

    def postdropTypeCheck(left, right):
        if not left.eqOrCoerce(right): return None
        if (left.label=='[]' and right.label=='[]') or \
           (left.label=='S'  and right.label=='S'):
            return lambda l,r: Box(l.type.join(r.type), l.raw[:-len(r.raw)] if l.raw[-len(r.raw):]==r.raw else l.raw)

    def predropTypeCheck(left, right):
        if not left.eqOrCoerce(right): return None
        if (left.label=='[]' and right.label=='[]') or \
           (left.label=='S'  and right.label=='S'):
            return lambda l,r: Box(l.type.join(r.type), l.raw[len(r.raw):] if l.raw[:len(r.raw)]==r.raw else l.raw)

    def starTypeCheck(left, right):
        def splice(lst,delimiter):
            accumulator = lst.raw[0]
            plus = lambda l,r: Box(l.type.join(r.type),l.raw+r.raw)     # Can't refer to plusTypeCheck, fix later
            for l in lst.raw[1:]:
                accumulator = plus(accumulator, delimiter)
                accumulator = plus(accumulator, l)
            return accumulator
        if left.label=='[]' and right.eqOrCoerce(left.param1):
            return splice
        if not left.eqOrCoerce(right): return None
        if left.label=='{}':
            return lambda l,r: Box(l.type.join(r.type), l.raw & r.raw)

    def slashTypeCheck(left, right):
        if left.label=='S' and right.label=='S':
            return lambda whole,delimiter: Box(Type('[]',param1=Type('S')), [Box(Type('S'),s) for s in whole.raw.split(delimiter.raw)])

    opTypeCheck = {
        '+':  plusTypeCheck,
        '.+': postfixTypeCheck,
        '+.': prefixTypeCheck,
        '-':  subTypeCheck,
        '.-': postdropTypeCheck,
        '-.': predropTypeCheck,
        '*':  starTypeCheck,
        '/':  slashTypeCheck
    }

    @staticmethod
    def evaluateBinop(tree, listTag, env):
        accumulator = evaluate(tree.children[0], env)
        for c in tree.children[1:]:
            assert isinstance(c, Token) and c.symbol.isNonterminal and c.tag==listTag and len(c.children)==2, c
            assert isinstance(c.children[0], Token) and c.children[0].symbol.isTerminal, c.children[0]
            value = evaluate(c.children[1], env)
            op = c.children[0].span
            print(f'evalBinop lhs={accumulator} op={op} rhs={value}')
            eval = Box.opTypeCheck[op](accumulator.type, value.type)
            assert eval is not None, f"Invalid types for operation: {accumulator.type} {op} {value.type}"
            accumulator = eval(accumulator, value)
        return accumulator

    @staticmethod
    def evaluateBinop1(tree, env):
        return Box.evaluateBinop(tree, "binop1_lst", env)

    @staticmethod
    def evaluateBinop2(tree, env):
        return Box.evaluateBinop(tree, "binop2_lst", env)

    @staticmethod
    def evaluateOrder(tree, env):
        if len(tree.seq)==0:  return Box(Type('[]',param1='empty'),[])
        result = [ evaluate(tree.seq[0], env) ]
        for subtree in tree.seq[1:]:
            element = evaluate(subtree,env)
            assert result[0].type.eqOrCoerce(element.type), f"Can't store element {element.type} inside [{result[0].type}]!"
            result.append(element)
        return Box(Type('[]', param1=result[0].type), result)

    @staticmethod
    def evaluateSet(tree, env):
        if len(tree.elements)==0: return Box(Type('{}',param1='empty'),frozenset())
        element = evaluate(tree.elements[0], env)
        elementType = element.type
        result = set([element])
        for subtree in tree.elements[1:]:
            element = evaluate(subtree, env)
            assert elementType.eqOrCoerce(element.type), f"Can't store element {element.type} inside \{{elementType}}!"
            result.add(element)
        return Box(Type('{}', param1=elementType), frozenset(result))


    @staticmethod
    def evaluateRecord(tree, env):
        result = Box(Type('[:]'), Environment())
        dump(tree)
        for child in tree.children:
            assert isinstance(child, AST.IdentVal), child
            assert not result.raw.contains(child.key), child.key
            value = evaluate(child.value, env)
            result.raw.insert(child.key, value.type, value)
        return result


    def unbox(self):
        if self.type.label=='{}':
            raw = frozenset(box.unbox() for box in self.raw)
        elif self.type.label in ('[]','[:]','{:}'):
            raw = [box.unbox() for box in self.raw]
        else:
            raw = self.raw
        return raw

from .execution import evaluate, Environment
