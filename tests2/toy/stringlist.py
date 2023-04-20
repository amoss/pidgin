# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import string

def toy_stringlist():
    '''Test lists of pidgin-style string literals.'''
    letters = string.ascii_lowercase + string.ascii_uppercase
    g = Grammar('atom')
    g.setDiscard(S(' \t\r\n',m='some'))
    g.addRule('atom', [N('str_lit')], [N('order')])
    g.addRule('order', [T('['), N('elem_lst',m='any'), T(']')])
    g.addRule('elem_lst', [N('atom'), T(',',m='optional')])
    g.addRule('str_lit', [T("'"), Glue(), S(['"'],True,m='any'), T('"'), Remove()],
                         [T('u('), Glue(), S([')'],True,m='any'), T(')'), Remove()])
    return g, \
'''[]
'hello"
u(world)
[u(x)]
[u(x) u(y)]
[u(x), u(y)]
[u(x), u(y),]
[u(x) ,u(y)]
[u(x) , u(y)]
['hello" 'world"]
[u(a) u(b) u(c)]
['a" 'b" 'c"]
[u(a)  u(b)   'c"]
[['x"] ['y"] ['z"]]'''.split('\n'),\
'''
[)
[,]
][
['a"
[u(a]
[['x"]'y"
'''.split('\n')

def toy_stringlist2():
    '''A: S | O   O: [ ] | [ P* A ,?] | [ A A+ ]   P: A ,   S: ' [^"]* " | u( [^)]* )

       Test lists of pidgin-style string literals with uniform but optional commas.'''
    letters = string.ascii_lowercase + string.ascii_uppercase
    g = Grammar('atom')
    g.setDiscard(S(' \t\r\n',m='some'))
    g.addRule('atom', [N('str_lit')], [N('order')])
    g.addRule('order', [T('['), T(']')],
                       [T('['), N('pair', m='any'), N('atom'), T(',',m='optional'), T(']')],
                       [T('['), N('atom'), N('atom', m='some'), T(']')])
    g.addRule('pair', [N('atom'), T(',')])
    g.addRule('str_lit', [T("'"), Glue(), S(['"'],True,m='any'), T('"'), Remove()],
                         [T('u('), Glue(), S([')'],True,m='any'), T(')'), Remove()])
    return g, \
'''[]
'hello"
u(world)
[u(x)]
[u(x) u(y)]
[u(x), u(y)]
[u(x), u(y),]
[u(x) ,u(y)]
[u(x) , u(y)]
[[], [], [], []]
[[], [], [], [],]
['hello" 'world"]
[u(a) u(b) u(c)]
['a" 'b" 'c"]
[u(a)  u(b)   'c"]
[['x"] ['y"] ['z"]]'''.split('\n'),\
'''
[)
[,]
][
['a"
[u(a]
[[] [], [], []]
[[] [], [] []]
[['x"]'y"
'''.split('\n')
