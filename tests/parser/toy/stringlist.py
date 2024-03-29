# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import string

def toy_stringlist():
    '''atom: str_lit | order   order: [ elem_lst* ]   elem_lst: atom?   str_lit: ' [^"]* " | u( [^)]* )

       Test lists of pidgin-style string literals.'''
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
'''.split('\n'), []

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
'''.split('\n'), []


def toy_numberlist():
    '''order: [ elem_lst* ]   elem_lst: atom?   atom: number | order   number: [0-9] Glue [0-9]* Remover

       Test lists of integer literals.'''
    letters = string.ascii_lowercase + string.ascii_uppercase
    g = Grammar('order')
    g.setDiscard(S(' \t\r\n',m='some'))
    g.addRule('atom', [N('number')], [N('order')])
    g.addRule('order', [T('['), N('elem_lst',m='any'), T(']')])
    g.addRule('elem_lst', [N('atom'), T(',',m='optional')])
    g.addRule('number', [S(string.digits), Glue(), S(string.digits,m='any'), Remove()])
    return g, \
'''[]
[1 23 45]'''.split('\n'), [], []

def toy_maybe2list():
    '''Atom: [0-9]+ | Order   Order: [ Atom? Atom? ]

       A (recursive) definition of a list that may contain up to two items. The better way to define this
       would be a choice of [ Atom ] | [ Atom Atom ] as it produces an unambiguous parse. This version is
       useful for examining ambiguity.
    '''
    g = Grammar("Atom")
    g.setDiscard(S(" \t\r\n", m="some"))

    g.addRule("Atom", [S(string.digits), Glue(), S(string.digits,m="any"), Remove()], [N("Order")])
    g.addRule("Order", [T('['), N("Atom", m="optional"), N("Atom",m="optional"), T("]")])

    return g, ['1', '123', '[]', '[1]', '[1 123]', '[[] 123]', '[[]]', '[[[]]]', '[[123] [[1] 123]]'], \
              ['', '123 1', '[] []', '[1 1 1]', '[[] [] []]'], \
              []


