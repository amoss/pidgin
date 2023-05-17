# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.
import string

def regex_stringstar():
    '''R: prefix word* suffix

       Test the use of star modifier on terminal strings in a grammar.'''
    g = Grammar('R')
    g.addRule('R', [T('prefix'), T('word','any'), T('suffix')])
    return g, ['prefixsuffix', 'prefixwordsuffix', 'prefixwordwordsuffix', 'prefixwordwordwordsuffix'], \
           ['', 'suffix', 'prefix', 'prefixworsuffix', 'prefixworddsuffix']

def regex_optional():
    '''R: x y? z

       Test the use of optional modifier on terminals in a grammar.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), T('y','optional'), T('z')])
    return g, ['xz', 'xyz'], \
           ['','x','z', 'xyyz', 'y']


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
    return g, ['l', 'lx', 'lxx', 'lxxx', 'lxxxx'], \
           ['', 'x', 'xx', 'll', 'rx', 'z', 'llxx']


def regex_starboundedleft2():
    '''R: x x*

       Test repetition of a terminal with an overlapping boundary on the left.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), T('x','any')])
    return g, ['x', 'xx', 'xxx', 'xxxx'], \
           ['', 'y', 'yxx', 'xxxy']


def regex_starboundedleft3():
    '''R: x W ; W: x*

       Test repetition of a terminal with an overlapping boundary on the left, where the repeating part is
       wrapped inside a non-terminal to test if the handle check consumes the extra symbol.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), N('W')])
    g.addRule('W', [T('x','any')])
    return g, ['x', 'xx', 'xxx', 'xxxx'], \
           ['', 'y', 'yxx', 'xxxy']


def regex_starboundedright():
    '''R: x* r

       Test repetition of a terminal with a non-overlapping boundary on the right.'''
    g = Grammar('R')
    g.addRule('R', [T('x','any'), T('r')])
    return g, ['r', 'xr', 'xxr', 'xxxr'], \
           ['l','xl','lx','x','xx','rx','rxx']


def regex_starboundedright2():
    '''R: x* x

       Test repetition of a terminal with an overlapping boundary on the right, equivalent to x+'''
    g = Grammar('R')
    g.addRule('R', [T('x','any'), T('x')])
    return g, ['x','xx','xxx','xxxx'], \
           ['l','lx','','xr']


def regex_starboundedboth():
    '''R: l x* r

       Test repetition of a terminal with a non-overlapping boundary on both sides.'''
    g = Grammar('R')
    g.addRule('R', [T('l'), T('x','any'), T('r')])
    return g, ['lr', 'lxr', 'lxxr', 'lxxxr'], \
           ['', 'x', 'xx', 'lx', 'lxx', 'xr', 'xxr']


def regex_starboundedboth2():
    '''R: x x* x

       Test repetition of a terminal with an overlapping boundary on both sides.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), T('x','any'), T('x')])
    return g, ['xx', 'xxx', 'xxxx'], ['','x','l','lxx','xxr']


def regex_choice():
    '''R: (x|y) (y|z) (z|k)

       Test sequence of choices with overlapping cases.'''
    g = Grammar('R')
    g.addRule('R', [N('Ca'), N('Cb'), N('Cc')])
    g.addRule('Ca', [T('x')], [T('y')])
    g.addRule('Cb', [T('y')], [T('z')])
    g.addRule('Cc', [T('z')], [T('k')])
    return g, ['xyz','xyk','xzz','xzk','yyz','yyk','yzz','yzk'], \
           ['xy','yk','xxx','']


def regex_choicestar():
    '''R: (x|y)* (y|z)* (z|k)*

       Test sequence of repeated choices with overlapping cases.'''
    g = Grammar('R')
    g.addRule('R', [N('Ca','any','greedy'), N('Cb','any','greedy'), N('Cc','any','greedy')])
    g.addRule('Ca', [T('x')], [T('y')])
    g.addRule('Cb', [T('y')], [T('z')])
    g.addRule('Cc', [T('z')], [T('k')])
    return g, ['', 'x', 'xx', 'xxx', 'y', 'yy', 'yyy', 'k', 'kk', 'kkk', 'zy', 'zyy', 'zyyy',
               'k', 'kz', 'kzz', 'kzzz', 'xyyk', 'xyyyzk'], \
           ['l', 'ky', 'kyy', 'kyyy', 'zx', 'zxx', 'zxxx', 'xzx', 'xkx']


def regex_selfalignunbounded():
    '''R: (x y)*

       Test self aligned repeating sequence with no boundaries.'''
    g = Grammar('R')
    g.addRule('R', [N('S','any','greedy')])
    g.addRule('S', [T('x'), T('y')])
    return g, ['', 'xy', 'xyxy', 'xyxyxy'], \
           ['xx','yy','xyx','xyyx']


def regex_selfalignboundedleft():
    '''R: l (x y)*

       Test self aligned repeating sequence with a non-overlapping boundary on the left.'''
    g = Grammar('R')
    g.addRule('R', [T('l'), N('S','any','greedy')])
    g.addRule('S', [T('x'), T('y')])
    return g, ['l', 'lxy', 'lxyxy', 'lxyxyxy'], \
           ['','xx','yy','xyx','xyyx', 'xy', 'xyxy', 'rxyxy', 'xyxyl']


def regex_selfalignboundedleft2():
    '''R: x (x y)*

       Test self aligned repeating sequence with an overlapping boundary on the left.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), N('S','any','greedy')])
    g.addRule('S', [T('x'), T('y')])
    return g, ['x', 'xxy', 'xxyxy', 'xxyxyxy'], \
           ['', 'xx', 'xxyy', 'xxyx', 'lx', 'xxyr']


def regex_selfalignboundedright():
    '''R: (x y)* r

       Test self aligned repeating sequence with a non-overlapping boundary on the right.'''
    g = Grammar('R')
    g.addRule('R', [N('S','any','greedy'), T('r')])
    g.addRule('S', [T('x'), T('y')])
    return g, ['r', 'xyr', 'xyxyr', 'xyxyxyr'], \
          ['', 'xr', 'xxr', 'xy', 'xyxy', 'xyxr', 'xyyr', 'xxyyr']


def regex_selfalignboundedright2():
    '''R: (x y)* x

       Test self aligned repeating sequence with an overlapping boundary on the right.'''
    g = Grammar('R')
    g.addRule('R', [N('S','any','greedy'), T('x')])
    g.addRule('S', [T('x'), T('y')])
    return g, ['x', 'xyx', 'xyxyx', 'xyxyxyx'], \
           ['', 'xy', 'xyxy', 'xyr', 'lxyx', 'xx', 'xyxx']


def regex_selfalignboundedboth():
    '''R: l (x y)* r

       Test self aligned repeating sequence with a non-overlapping boundary on both sides.'''
    g = Grammar('R')
    g.addRule('R', [T('l'), N('S','any','greedy'), T('r')])
    g.addRule('S', [T('x'), T('y')])
    return g, ['lr', 'lxyr', 'lxyxyr', 'lxyxyxyr'], \
           ['l', 'r', 'lxy', 'xyr', 'lxr', 'lyr', 'lxyxr', 'lxxyyr']


def regex_selfalignboundedboth2():
    '''R: x (x y)* x

       Test self aligned repeating sequence with an overlapping boundary on both sides.'''
    g = Grammar('R')
    g.addRule('R', [T('x'), N('S','any','greedy'), T('x')])
    g.addRule('S', [T('x'), T('y')])
    return g, ['xx', 'xxyx', 'xxyxyx', 'xxyxyxyx'], \
           ['', 'x', 'xxx', 'xxy', 'xyx', 'lxx', 'xxr', 'lxxyx', 'xxyxx', 'xyx']

def regex_glue():
    '''R: [a-z] Glue [a-z0-9]* Remover

       Test use of glue between terminals.'''
    g = Grammar('R')
    g.setDiscard(S(' \t\r\n',m='some'))
    g.addRule('R', [S(string.ascii_letters), Glue(), S(string.ascii_letters+string.digits,m='any'), Remove()])
    return g, ['x', 'y', 'x123', 'xyyy'], ['', '1x', 'x y']

def regex_glue2():
    '''R: [a-z] Glue [a-z0-9]* Remover

       Test use of glue between terminals.'''
    g = Grammar('R')
    g.setDiscard(S(' \t\r\n',m='some'))
    g.addRule('R', [N('I',m='some')])
    g.addRule('I', [S(string.ascii_letters), Glue(), S(string.ascii_letters+string.digits,m='any'), Remove()])
    return g, ['x', 'y', 'x123', 'xyyy', 'x y z', 'xy yz zu', 'hello world','zippy    do   da'], ['', '1x', 'x 1y']
