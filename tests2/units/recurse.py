# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

def recurse_degenseq():
    '''R: R* x

       Test degenerate form of terminal repetition, same language as x+ but combinatorially ambiguous without
       greediness. Left-recursive form.'''
    g = Grammar('R')
    g.addRule('R', [N('R','any','greedy'), T('x')])
    return g, ['x', 'xx', 'xxx', 'xxxx'], \
           ['', 'lx', 'xr'], \
           []


def recurse_degenseq2():
    '''R: x R*

       Test degenerate form of terminal repetition, same language as x+ but combinatorially ambiguous without
       greediness. Right-recursive form.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), N('R','any','greedy')])
    return g, ['x', 'xx', 'xxx', 'xxxx'], \
           ['', 'lx', 'xr'], \
           []


def recurse_degenseq3():
    '''R: (R x)*

       Test degenerate form of terminal repetition, same language as x* but combinatorially ambiguous without
       greediness. Left-recursive form. Successful traces have a prefix that reduces empty to R before starting
       to shift.'''
    g = Grammar('R')
    g.addRule('R',  [N('Ri','any','greedy')])
    g.addRule('Ri', [N('R'), T('x')])
    return g, ['', 'x', 'xx', 'xxx', 'xxxx'], \
           ['lx', 'xr'], \
           []


def recurse_degenseq4():
    '''R: (x R)*

       Test degenerate form of terminal repetition, same language as x* but combinatorially ambiguous without
       greediness. Right-recursive form.'''
    g = Grammar('R')
    g.addRule('R',  [N('Ri','any','greedy')])
    g.addRule('Ri', [T('x'), N('R')])
    return g, ['', 'x', 'xx', 'xxx', 'xxxx'], \
           ['lx', 'xr'], \
           []


def recurse_nests():
    '''R: l R* r

       Test bracket nesting. Not degenerate as sub-sequences cannot overlap?'''
    g = Grammar('R')
    g.addRule('R', [T('l'), N('R','any','greedy'), T('r')])
    return g, ['lr','llrr','llrlrr','lllrrlrlrr', 'llrllrrlrr', 'llrllrlrrlrr'], \
           ['', 'l', 'r', 'll', 'rr', 'llr', 'lrr', 'rl', 'lllrr', 'llrlr', 'llrrr', 'lllrlrrrr'], \
           []


def recurse_nests2():
    '''R: (l R r)*

       Test bracket nesting. Not degenerate as sub-sequences cannot overlap?'''
    g = Grammar('R')
    g.addRule('R',  [N('Ri','any','greedy')])
    g.addRule('Ri', [T('l'), N('R'), T('r')])
    return g, ['','lr','llrr','llrlrr','lllrrlrlrr', 'llrllrrlrr', 'llrllrlrrlrr'], \
           ['l', 'r', 'll', 'rr', 'llr', 'lrr', 'rl', 'lllrr', 'llrlr', 'llrrr', 'lllrlrrrr'], \
           []


def recurse_partialnests():
    '''R: l* R r*

       Test bracket (partial-) nesting. Impossible to match as requires an infinitely deep
       nesting of R.'''
    g = Grammar('R')
    g.addRule('R', [T('l','any','greedy'), N('R'), T('r','any','greedy')])
    return g, [], ['', 'l', 'll', 'lll', 'r', 'rr', 'rrr', 'lllrlr', 'lllrrrrrlr', 'rrrlll',
              'x','xx','xxx','xxxx'], \
              []


def recurse_termplusvianonterm():
    '''R: S* x ; S: x

       Test that non-terminal stars are equivalent to terminal stars, simulate x+ via depth-limited recursion.'''
    g = Grammar('R')
    g.addRule('R', [N('S','any','greedy'), T('x')])
    g.addRule('S', [T('x')])
    return g, ['x','xx','xxx','xxxx'], \
           ['','lx','xr'], \
           []


def recurse_termplusvianonterm2():
    '''R: S* l r ; S: l r

       Test that non-terminal stars are equivalent to terminal stars, simulate (l r)+ via depth-limited recursion.'''
    g = Grammar('R')
    g.addRule('R', [N('S','any','greedy'), T('l'), T('r')])
    g.addRule('S', [T('l'), T('r')])
    return g, ['lr','lrlr','lrlrlr','lrlrlrlr'], \
           ['','l','r','lxr','xlr','lrx','lrl','lrr','rlr'], \
           []


def recurse_parensseq():
    '''E: (x | < E >)(+ E)*

       Test a parenthesized sequence with a single operator.'''
    g = Grammar('E')
    g.addRule('E', [T('x'), N('Et','any','greedy')], [T('<'), N('E'), T('>'), N('Et','any','greedy')])
    g.addRule('Et', [T('+'), N('E')])
    return g, ['x','x+x','x+x+x','<x>','<x>+x','x+<x>','<x>+<x>','<x+x>','<x+<x>>','<<x+x>+<x>>+<x>'], \
           ['','xx','<x','x>','<x>>','x+','<x+x','x+x>','x+<x'], \
           []


def recurse_parensseq2():
    '''E: F (/ F)* ; F: (x | < E >)(+ E)*

       Test a parenthesized sequence with two prioritized operators.'''
    g = Grammar('E')
    g.addRule('E',  [N('F'), N('Et','any','greedy')])
    g.addRule('Et', [T('/'), N('F')])
    g.addRule('F',  [T('x'), N('Ft','any','greedy')], [T('<'), N('E'), T('>'), N('Ft','any','greedy')])
    g.addRule('Ft', [T('+'), N('E')])
    return g, ['x', 'x+x', 'x+x+x', '<x>', '<x>+x', 'x+<x>', '<x>+<x>', '<x+x>', '<x+<x>>', '<<x+x>+<x>>+<x>',
               'x/x', 'x/x/x', 'x/x+x', 'x+x/x', 'x/<x+x>', '<x/x>+x', '<<x>/x+x>/<x+x>'], \
           ['','xx','<x','x>','<x>>','x+','<x+x','x+x>','x+<x','x/','x/x/','x/x>','<x/x','<x>/','/x'], \
           []
