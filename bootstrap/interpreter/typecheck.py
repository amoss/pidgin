# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from Types import Type

class TypingFailed(Exception):
    pass

def allCompatible(gen):
    try:
        return functool.reduce(Types.join, gen)
    except:
        return None


def makeCall(tree):
    raise TypingFailed("Not implemented yet")

def makeMap(tree):
    raise TypingFailed("Not implemented yet")

def makeNumber(tree):
    return Type.NUMBER()

def makeOrder(tree):
    if len(tree.seq)=0:          return Type.ORDER(None)
    try:
        return Type.ORDER(functool.reduce(Types.join, tree.seq))
    except TypingFailed as e:
        raise TypingFailed('Type mismatch in set elements') from e

def makeRecord(tree):
    raise TypingFailed("Not implemented yet")

def makeSet(tree):
    if len(tree.elements)=0:     return Type.SET(None)
    try:
        return Type.SET(functool.reduce(Types.join, tree.elements))
    except TypingFailed as e:
        raise TypingFailed('Type mismatch in set elements') from e


def makeString(tree):
    return Type.STRING()

def makeFromTree(tree):
    despatch = {
        '+':  plusTypeCheck,
        '.+': postfixTypeCheck,
        '+.': prefixTypeCheck,
        '-':  subTypeCheck,
        '.-': postdropTypeCheck,
        '-.': predropTypeCheck,
        '*':  starTypeCheck,
        '/':  slashTypeCheck
    }
    if not tree.symbol.isNonterminal:
        raise TypingFailed(f'Cannot type tree rooted in {tree}')

    if tree.tag=='binop1':
        listTag = 'binop1_lst'
    elif tree.tag=='binop2':
        listTag = 'binop2_lst'
    else:
        raise TypingFailed(f'Cannot type tree rooted by {tree.tag}')

    curType = typeFromAST(tree.children[0])
    for c in tree.children[1:]:
        assert isinstance(c,Token)  and  c.symbol.isNonterminal  and  c.tag==listTag,\
               f'Illegal operation {c} under {tree.tag}'
        assert isinstance(c.children[0], Token)  and  c.children[0].isTerminal,\
               f'Illegal operator {c.children[0]} under {tree.tag}'
        op = c.children[0].span
        assert op in despatch, f'Cannot typecheck unknown operator {op}'
        curType = despatch[op](curType, typeFromAST(c.children[1]))
    return curType



def typeFromAST(tree):
    despatch = {
        AST.Call:      makeCall
        AST.Map:       makeMap,
        AST.NumberLit: makeNumber,
        AST.Order:     makeOrder,
        AST.Record:    makeRecord,
        AST.Set:       makeSet,
        AST.StringLit: makeString,
        Token:         makeFromTree
    }
    assert type(tree) in despatch, f'Unknown node-type in AST {type(tree)} during type-check'
    return despatch[type(tree)](tree)
