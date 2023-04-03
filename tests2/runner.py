import os, sys
rootDir= os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)
#from bootstrap.grammar import Grammar
import monster
Grammar = monster.Grammar

import shutil
import traceback

def T(val, m=None, s=None):
    if m is None:
        if isinstance(val,str):
            return Grammar.TermString(val)
        return Grammar.TermSet(val)
    if isinstance(val,str):
        return Grammar.TermString(val, modifier=m)
    return Grammar.TermSet(val, modifier=m, strength=s)


def N(name, modifier='just', strength='greedy'):
    return Grammar.Nonterminal(name, modifier=modifier, strength=strength)


def regex_seq():
    '''R: x y z

       Test sequencing of terminals in a grammar.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), T('y'), T('z')])
    return g


def regex_seqstar():
    '''R: x* y* z*

       Test repetition of terminals within a sequence.'''
    g = Grammar('R')
    g.addRule('R', [T('x','any'), T('y','any'), T('z','any')])
    return g
    # TODO: Where are the repeating shift edges for the stars?


def regex_starboundedleft():
    '''R: l x*

       Test repetition of a terminal with a non-overlapping boundary on the left.'''
    g = Grammar('R')
    g.addRule('R', [T('l'), T('x','any')])
    return g
    # TODO: Missing shifts for repetition in stars, missing reduce cases for barriers


def regex_starboundedleft2():
    '''R: x x*

       Test repetition of a terminal with an overlapping boundary on the left.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), T('x','any')])
    return g


def regex_starboundedright():
    '''R: x* r

       Test repetition of a terminal with a non-overlapping boundary on the right.'''
    g = Grammar('R')
    g.addRule('R', [T('x','any'), T('r')])
    return g


def regex_starboundedright2():
    '''R: x* x

       Test repetition of a terminal with an overlapping boundary on the right.'''
    g = Grammar('R')
    g.addRule('R', [T('x','any'), T('x')])
    return g
    # TODO: Barriers are missing on shift edges


def regex_starboundedboth():
    '''R: l x* r

       Test repetition of a terminal with a non-overlapping boundary on both sides.'''
    g = Grammar('R')
    g.addRule('R', [T('l'), T('x','any'), T('r')])
    return g


def regex_starboundedboth2():
    '''R: x x*

       Test repetition of a terminal with an overlapping boundary on both sides.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), T('x','any'), T('x')])
    return g


def regex_choice():
    '''R: (x|y) (y|z) (z|k)

       Test sequence of choices with overlapping cases.'''
    g = Grammar('R')
    g.addRule('R', [N('Ca'), N('Cb'), N('Cc')])
    g.addRule('Ca', [T('x')], [T('y')])
    g.addRule('Cb', [T('y')], [T('z')])
    g.addRule('Cc', [T('z')], [T('k')])
    return g


def regex_choicestar():
    '''R: (x|y)* (y|z)* (z|k)*

       Test sequence of repeated choices with overlapping cases.'''
    g = Grammar('R')
    g.addRule('R', [N('Ca','any','greedy'), N('Cb','any','greedy'), N('Cc','any','greedy')])
    g.addRule('Ca', [T('x')], [T('y')])
    g.addRule('Cb', [T('y')], [T('z')])
    g.addRule('Cc', [T('z')], [T('k')])
    return g
    # TODO: Check this carefully


def regex_selfalignunbounded():
    '''R: (x y)*

       Test self aligned repeating sequence with no boundaries.'''
    g = Grammar('R')
    g.addRule('R', [N('S','any','greedy')])
    g.addRule('S', [T('x'), T('y')])
    return g
    # TODO: Barrier exits are unclear, but this could be correct


def regex_selfalignboundedleft():
    '''R: l (x y)*

       Test self aligned repeating sequence with a non-overlapping boundary on the left.'''
    g = Grammar('R')
    g.addRule('R', [T('l'), N('S','any','greedy')])
    g.addRule('S', [T('x'), T('y')])
    return g


def regex_selfalignboundedleft2():
    '''R: x (x y)*

       Test self aligned repeating sequence with an overlapping boundary on the left.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), N('S','any','greedy')])
    g.addRule('S', [T('x'), T('y')])
    return g


def regex_selfalignboundedright():
    '''R: (x y)* r

       Test self aligned repeating sequence with a non-overlapping boundary on the right.'''
    g = Grammar('R')
    g.addRule('R', [N('S','any','greedy'), T('r')])
    g.addRule('S', [T('x'), T('y')])
    return g


def regex_selfalignboundedright2():
    '''R: (x y)* x

       Test self aligned repeating sequence with an overlapping boundary on the right.'''
    g = Grammar('R')
    g.addRule('R', [N('S','any','greedy'), T('x')])
    g.addRule('S', [T('x'), T('y')])
    return g
    # TODO: Could be correct, but barrier exits are unclear


def regex_selfalignboundedboth():
    '''R: l (x y)* r

       Test self aligned repeating sequence with a non-overlapping boundary on both sides.'''
    g = Grammar('R')
    g.addRule('R', [T('l'), N('S','any','greedy'), T('r')])
    g.addRule('S', [T('x'), T('y')])
    return g



def regex_selfalignboundedboth2():
    '''R: x (x y)* x

       Test self aligned repeating sequence with an overlapping boundary on both sides.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), N('S','any','greedy'), T('x')])
    g.addRule('S', [T('x'), T('y')])
    return g


def recurse_degenseq():
    '''R: R* x

       Test degenerate form of terminal repetition, same language as x+ but combinatorially ambiguous without
       greediness. Left-recursive form.'''
    g = Grammar('R')
    g.addRule('R', [N('R','any','greedy'), T('x')])
    return g


def recurse_degenseq2():
    '''R: x R*

       Test degenerate form of terminal repetition, same language as x+ but combinatorially ambiguous without
       greediness. Right-recursive form.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), N('R','any','greedy')])
    return g


def recurse_degenseq3():
    '''R: (R x)*

       Test degenerate form of terminal repetition, same language as x* but combinatorially ambiguous without
       greediness. Left-recursive form.'''
    g = Grammar('R')
    g.addRule('R',  [N('Ri','any','greedy')])
    g.addRule('Ri', [N('R'), T('x')])
    return


def recurse_degenseq4():
    '''R: (x R)*

       Test degenerate form of terminal repetition, same language as x* but combinatorially ambiguous without
       greediness. Right-recursive form.'''
    g = Grammar('R')
    g.addRule('R',  [N('Ri','any','greedy')])
    g.addRule('Ri', [T('x'), N('R')])
    return g


def recurse_nests():
    '''R: l R* r

       Test bracket nesting. Not degenerate as sub-sequences cannot overlap?'''
    g = Grammar('R')
    g.addRule('R', [T('l'), N('R','any','greedy'), T('r')])
    return g


def recurse_nests2():
    '''R: (l R r)*

       Test bracket nesting. Not degenerate as sub-sequences cannot overlap?'''
    g = Grammar('R')
    g.addRule('R',  [N('R','any','greedy')])
    g.addRule('Ri', [T('l'), N('R'), T('r')])
    return g


def recurse_partialnests():
    '''R: l* R r*

       Test bracket (partial-) nesting. No idea if degenerate or not, kind of wondering what language this generates, lol'''
    g = Grammar('R')
    g.addRule('R', [T('l','any','greedy'), N('R'), T('r','any','greedy')])
    return g
    # TODO: Don't know if this works or not, but there are missing reduce cases for the barriers


units = [
    regex_seq,
    regex_seqstar,
    regex_starboundedleft,
    regex_starboundedleft2,
    regex_starboundedright,
    regex_starboundedright2,
    regex_starboundedboth,
    regex_starboundedboth2,
    regex_choice,
    regex_choicestar,
    regex_selfalignunbounded,
    regex_selfalignboundedleft,
    regex_selfalignboundedleft2,
    regex_selfalignboundedright,
    regex_selfalignboundedright2,
    regex_selfalignboundedboth,
    regex_selfalignboundedboth2,

    recurse_degenseq,
    recurse_degenseq2,
    recurse_degenseq3,
    recurse_degenseq4,
    recurse_nests,
    recurse_partialnests
]

# Clean old results
target = os.path.join(rootDir,"unitResults")
for name in os.listdir(target):
    if name==".keep" or name=="index.md":  continue
    dir = os.path.join(target,name)
    print(f"Cleaning {dir}")
    shutil.rmtree(dir)

index = open( os.path.join(target,"index.md"), "wt")
for u in units:
    description   = u.__doc__
    lines         = description.split('\n')
    simple        = lines[0]
    justification = "\n".join(lines[2:])
    name          = u.__qualname__

    print(f'\n## {name}', file=index)
    print(f'`{simple}`', file=index)
    print(justification, file=index)
    print(f'\n![eclr machine]({name}/eclr.dot.png)', file=index)

    try:
        grammar = u()
        grammar.dump()
        dir = os.path.join(target,name)
        os.makedirs(dir, exist_ok=True)
        automaton = monster.Automaton(grammar)
        automaton.dot( open(os.path.join(dir,"eclr.dot"), "wt") )
    except:
        traceback.print_exc()

