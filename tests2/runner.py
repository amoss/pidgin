import os, sys
rootDir= os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)
#from bootstrap.grammar import Grammar
import monster
Grammar = monster.Grammar

import shutil
import traceback

GRAY = "\033[0;37m"
RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
END = "\033[0m"

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
    return g, ['xyz'], \
           ['xxy','yyz','x','xy','yz']


def regex_seqstar():
    '''R: x* y* z*

       Test repetition of terminals within a sequence.'''
    g = Grammar('R')
    g.addRule('R', [T('x','any'), T('y','any'), T('z','any')])
    return g, ['', 'x', 'xx' ,'xxx', 'xxxx', 'y', 'yy', 'yyy', 'yyyy', 'z', 'zz', 'zzz', 'zzzz',
               'xy', 'xxy', 'xyy', 'xxyyz', 'xyz', 'xyzzz', 'yzz'], \
           ['yx', 'zx', 'zy', 'xjz', 'zi']


def regex_starboundedleft():
    '''R: l x*

       Test repetition of a terminal with a non-overlapping boundary on the left.'''
    g = Grammar('R')
    g.addRule('R', [T('l'), T('x','any')])
    return g, [], []


def regex_starboundedleft2():
    '''R: x x*

       Test repetition of a terminal with an overlapping boundary on the left.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), T('x','any')])
    return g, [], []


def regex_starboundedright():
    '''R: x* r

       Test repetition of a terminal with a non-overlapping boundary on the right.'''
    g = Grammar('R')
    g.addRule('R', [T('x','any'), T('r')])
    return g, [], []


def regex_starboundedright2():
    '''R: x* x

       Test repetition of a terminal with an overlapping boundary on the right.'''
    g = Grammar('R')
    g.addRule('R', [T('x','any'), T('x')])
    return g, [], []


def regex_starboundedboth():
    '''R: l x* r

       Test repetition of a terminal with a non-overlapping boundary on both sides.'''
    g = Grammar('R')
    g.addRule('R', [T('l'), T('x','any'), T('r')])
    return g, [], []


def regex_starboundedboth2():
    '''R: x x*

       Test repetition of a terminal with an overlapping boundary on both sides.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), T('x','any'), T('x')])
    return g, [], []


def regex_choice():
    '''R: (x|y) (y|z) (z|k)

       Test sequence of choices with overlapping cases.'''
    g = Grammar('R')
    g.addRule('R', [N('Ca'), N('Cb'), N('Cc')])
    g.addRule('Ca', [T('x')], [T('y')])
    g.addRule('Cb', [T('y')], [T('z')])
    g.addRule('Cc', [T('z')], [T('k')])
    return g, [], []


def regex_choicestar():
    '''R: (x|y)* (y|z)* (z|k)*

       Test sequence of repeated choices with overlapping cases.'''
    g = Grammar('R')
    g.addRule('R', [N('Ca','any','greedy'), N('Cb','any','greedy'), N('Cc','any','greedy')])
    g.addRule('Ca', [T('x')], [T('y')])
    g.addRule('Cb', [T('y')], [T('z')])
    g.addRule('Cc', [T('z')], [T('k')])
    return g, [], []
    # TODO: Check this carefully


def regex_selfalignunbounded():
    '''R: (x y)*

       Test self aligned repeating sequence with no boundaries.'''
    g = Grammar('R')
    g.addRule('R', [N('S','any','greedy')])
    g.addRule('S', [T('x'), T('y')])
    return g, [], []
    # TODO: Barrier exits are unclear, but this could be correct


def regex_selfalignboundedleft():
    '''R: l (x y)*

       Test self aligned repeating sequence with a non-overlapping boundary on the left.'''
    g = Grammar('R')
    g.addRule('R', [T('l'), N('S','any','greedy')])
    g.addRule('S', [T('x'), T('y')])
    return g, [], []


def regex_selfalignboundedleft2():
    '''R: x (x y)*

       Test self aligned repeating sequence with an overlapping boundary on the left.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), N('S','any','greedy')])
    g.addRule('S', [T('x'), T('y')])
    return g, [], []


def regex_selfalignboundedright():
    '''R: (x y)* r

       Test self aligned repeating sequence with a non-overlapping boundary on the right.'''
    g = Grammar('R')
    g.addRule('R', [N('S','any','greedy'), T('r')])
    g.addRule('S', [T('x'), T('y')])
    return g, [], []


def regex_selfalignboundedright2():
    '''R: (x y)* x

       Test self aligned repeating sequence with an overlapping boundary on the right.'''
    g = Grammar('R')
    g.addRule('R', [N('S','any','greedy'), T('x')])
    g.addRule('S', [T('x'), T('y')])
    return g, [], []
    # TODO: Could be correct, but barrier exits are unclear


def regex_selfalignboundedboth():
    '''R: l (x y)* r

       Test self aligned repeating sequence with a non-overlapping boundary on both sides.'''
    g = Grammar('R')
    g.addRule('R', [T('l'), N('S','any','greedy'), T('r')])
    g.addRule('S', [T('x'), T('y')])
    return g, [], []



def regex_selfalignboundedboth2():
    '''R: x (x y)* x

       Test self aligned repeating sequence with an overlapping boundary on both sides.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), N('S','any','greedy'), T('x')])
    g.addRule('S', [T('x'), T('y')])
    return g, [], []


def recurse_degenseq():
    '''R: R* x

       Test degenerate form of terminal repetition, same language as x+ but combinatorially ambiguous without
       greediness. Left-recursive form.'''
    g = Grammar('R')
    g.addRule('R', [N('R','any','greedy'), T('x')])
    return g, [], []


def recurse_degenseq2():
    '''R: x R*

       Test degenerate form of terminal repetition, same language as x+ but combinatorially ambiguous without
       greediness. Right-recursive form.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), N('R','any','greedy')])
    return g, [], []


def recurse_degenseq3():
    '''R: (R x)*

       Test degenerate form of terminal repetition, same language as x* but combinatorially ambiguous without
       greediness. Left-recursive form.'''
    g = Grammar('R')
    g.addRule('R',  [N('Ri','any','greedy')])
    g.addRule('Ri', [N('R'), T('x')])
    return g, [], []

    # TODO: No initial shift to kickstart the parse, needs to reduce an empty R first. Compare with other form.


def recurse_degenseq4():
    '''R: (x R)*

       Test degenerate form of terminal repetition, same language as x* but combinatorially ambiguous without
       greediness. Right-recursive form.'''
    g = Grammar('R')
    g.addRule('R',  [N('Ri','any','greedy')])
    g.addRule('Ri', [T('x'), N('R')])
    return g, [], []


def recurse_nests():
    '''R: l R* r

       Test bracket nesting. Not degenerate as sub-sequences cannot overlap?'''
    g = Grammar('R')
    g.addRule('R', [T('l'), N('R','any','greedy'), T('r')])
    return g, [], []


def recurse_nests2():
    '''R: (l R r)*

       Test bracket nesting. Not degenerate as sub-sequences cannot overlap?'''
    g = Grammar('R')
    g.addRule('R',  [N('Ri','any','greedy')])
    g.addRule('Ri', [T('l'), N('R'), T('r')])
    return g, [], []


def recurse_partialnests():
    '''R: l* R r*

       Test bracket (partial-) nesting. No idea if degenerate or not, kind of wondering what language this generates, lol'''
    g = Grammar('R')
    g.addRule('R', [T('l','any','greedy'), N('R'), T('r','any','greedy')])
    return g, [], []
    # TODO: Don't know if this works or not, but there are missing reduce cases for the barriers


def recurse_termplusvianonterm():
    '''R: S* x ; S: x

       Test that non-terminal stars are equivalent to terminal stars, simulate x+ via depth-limited recursion.'''
    g = Grammar('R')
    g.addRule('R', [N('S','any','greedy'), T('x')])
    g.addRule('S', [T('x')])
    return g, [], []


def recurse_termplusvianonterm2():
    '''R: S* l r ; S: l r

       Test that non-terminal stars are equivalent to terminal stars, simulate (l r)+ via depth-limited recursion.'''
    g = Grammar('R')
    g.addRule('R', [N('S','any','greedy'), T('l'), T('r')])
    g.addRule('S', [T('l'), T('r')])
    return g, [], []


def recurse_parensseq():
    '''E: (x | < E >)(+ E)*

       Test a parenthesized sequence with a single operator.'''
    g = Grammar('E')
    g.addRule('E', [T('x'), N('Et','any','greedy')], [T('<'), N('E'), T('>'), N('Et','any','greedy')])
    g.addRule('Et', [T('+'), N('E')])
    return g, [], []


def recurse_parensseq2():
    '''E: F (/ F)* ; F: (x | < E >)(+ E)*

       Test a parenthesized sequence with two prioritized operators.'''
    g = Grammar('E')
    g.addRule('E',  [N('F'), N('Et','any','greedy')])
    g.addRule('Et', [T('/'), N('F')])
    g.addRule('F',  [T('x'), N('Ft','any','greedy')], [T('<'), N('E'), T('>'), N('Ft','any','greedy')])
    g.addRule('Ft', [T('x'), N('E')])
    return g, [], []



units = [ v for k,v in sorted(globals().items())
            if k[:6]=='regex_' or k[:8]=='recurse_' ]

# Clean old results
target = os.path.join(rootDir,"unitResults")
for name in os.listdir(target):
    if name==".keep" or name=="index.md" or name=='.DS_Store':  continue
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
        grammar, positive, negative = u()
        dir = os.path.join(target,name)
        os.makedirs(dir, exist_ok=True)
        automaton = monster.Automaton(grammar)
        automaton.dot( open(os.path.join(dir,"eclr.dot"), "wt") )

        for i,p in enumerate(positive):
            results = [r for r in automaton.execute(p, True)]
            automaton.trace.output( open(os.path.join(dir,f'p{i}.dot'),'wt') )
            if len(results)==0:
                print(f'{RED}Failed on {name} positive {i} {p}{END}')
            else:
                print(f'{GREEN}Passed on {name} positive {i} {p}{END}')
        for i,n in enumerate(negative):
            results = [r for r in automaton.execute(n, True)]
            automaton.trace.output( open(os.path.join(dir,f'n{i}.dot'),'wt') )
            if len(results)>0:
                print(f'{RED}Failed on {name} negative {i} {n}{END}')
            else:
                print(f'{GREEN}Passed on {name} negative {i} {n}{END}')
    except:
        traceback.print_exc()

