# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import string

def pidgin_expr():
    '''Test subset of pidgin for literal expressions.'''
    letters = string.ascii_lowercase + string.ascii_uppercase
    g = Grammar('binop1')
    g.addRule('binop1', [N('binop2'), N('binop1_lst',m='any')])
    g.addRule('binop1_lst', [T('.+'), N('binop2')],
                            [T('+.'), N('binop2')],
                            [T('.-'), N('binop2')],
                            [T('-.'), N('binop2')],
                            [T('+'),  N('binop2')],
                            [T('-'),  N('binop2')])
    g.addRule('binop2', [N('binop3'), N('binop2_lst',m='any')])
    g.addRule('binop2_lst', [T('*'), N('binop3')],
                            [T('/'), N('binop3')])
    g.addRule('binop3', [N('binop4'), N('binop3_lst',m='any')])
    g.addRule('binop3_lst', [T('@'), N('binop4')])
    g.addRule('binop4', [N('atom')],
                        [N('ident'), T('!'), N('atom')])
    g.addRule('atom', [T('true')],
                      [T('false')],
                      [S(string.digits,m='some')],
                      [N('ident')],
                      [N('str_lit')],
                      [N('set')],
                      [N('map')],
                      [N('order')],
                      [T('('),N('binop1'),T(')')])
    g.addRule('set',   [T('{'), N('elem_lst',m='optional'), T('}')])
    g.addRule('order', [T('['), N('elem_lst',m='optional'), T(']')])
    g.addRule('map',   [T('{'), N('elem_kv',m='some'), T('}')],
                       [T('{'), T(':'), T('}')])
    g.addRule('elem_kv',  [N('binop1'), T(':'), N('binop1'), T(',',m='optional')])
    g.addRule('elem_lst', [N('repeat_elem',m='any'), N('final_elem')])
    g.addRule('repeat_elem', [N('binop1'),T(',',m='optional')])
    g.addRule('final_elem', [N('binop1')])
    g.addRule('str_lit', [T("'"), S(['"'],True,m='any'), T('"')], [T('u('), S([')'],True,m='any'), T(')')])
    g.addRule('ident', [S(list(letters)+['_']),S(list(letters+string.digits)+['_'], m='any')])

# TODO: Put spaces back in after we sort out glue
    return g, \
'''[]
{}
{:}
'hello"
X!Y
X!'world"
['a"'b"'c"]
{'a"'b"'c"}
{'a":'"'b":'"'c":'"}
{'a":[X!'a"]'b":[X!'b"]'c":[]}
{'name":{[N!'a"][T!'b"]}}
{'name":{[N!'a"][T!'a",T!'b",T!'c"]}}
{'expr":{[N!'atom"][N!'binop1"]}}
u(abc)
'abc"
23
u()
'"
u(öäå123)
'öäå123"
u(😀)
'😀"
u(<>[]{}😍😍😝)
'<>[]{}😍😍😝"
u(🤪⇒℞⟪⟫)
'🤪⇒℞⟪⟫"
u( 	)
[1 23 4 567]
[3,33]
{2 3 4}
{ {} {1} }
[ {} {1} {2} ]
[{},{1},{2}]
{3:2}
{u(hello):'world", u(who):333}
{{}:{}[2]:7}
u(true)+true
u(,,,)
foo+blah
22+43/66.+[]
x+y@[2,2]+z@pos
'''.split('\n'), []
