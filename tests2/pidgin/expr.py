# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import string

def pidgin_expr():
    '''Test subset of pidgin for literal expressions.'''
    letters = string.ascii_lowercase + string.ascii_uppercase
    g = Grammar('binop1')
    g.setDiscard(S(' \t\r\n',m='some'))
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
                      [S(string.digits), Glue(), S(string.digits,m='any'), Remove()],
                      [N('ident')],
                      [N('str_lit')],
                      [N('set')],
                      [N('map')],
                      [N('order')],
                      [T('('),N('binop1'),T(')')])
    g.addRule('set', [T('{'), T('}')],
                     [T('{'), N('order_pair', m='any'), N('binop1'), T(',',m='optional'), T('}')],
                     [T('{'), N('binop1'), N('binop1', m='some'), T('}')])
    g.addRule('order', [T('['), T(']')],
                       [T('['), N('order_pair', m='any'), N('binop1'), T(',',m='optional'), T(']')],
                       [T('['), N('binop1'), N('binop1', m='some'), T(']')])
    g.addRule('order_pair', [N('binop1'), T(',')])
    g.addRule('map',   [T('{'), T(':'), T('}')],
                       [T('{'), N('kv_comma',m='any'), N('binop1'), T(':'), N('binop1'), T(',',m='optional'), T('}')],
                       [T('{'), N('kv_pair'), N('kv_pair',m='some'), T('}')])
    g.addRule('kv_pair',  [N('binop1'), T(':'), N('binop1')])
    g.addRule('kv_comma', [N('binop1'), T(':'), N('binop1'), T(',')])
    g.addRule('str_lit', [T("'"), Glue(), S(['"'],True,m='any'), T('"'), Remove()],
                         [T('<<'), Glue(), N('str_lit2',m='any'), T('>>'), Remove()])
    g.addRule('str_lit2', [S([">"],True)], [T('>'), S([">"],True)])
    g.addRule('ident', [S(list(letters)+['_']), Glue(), S(list(letters+string.digits)+['_'], m='any'), Remove()])

    return g, \
'''[]
{}
{:}
'hello"
X!Y
X!'world"
['a" 'b" 'c"]
['a"  'b"'c"]
{'a" 	'b"  'c"}
{'a":'"'b":'"'c":'"}
{'a":[X!'a"]'b":[X!'b"]'c":[]}
{'name":{[N!'a"][T!'b"]}}
{'name":{[N!'a"][T!'a",T!'b",T!'c"]}}
{'expr":{[N!'atom"][N!'binop1"]}}
<<abc>>
'abc"
23
<<>>
'"
<<öäå123>>
'öäå123"
<<😀>>
'😀"
<<<>[]{}😍😍😝>>
'<>[]{}😍😍😝"
<<🤪⇒℞⟪⟫>>
'🤪⇒℞⟪⟫"
<< 	>>
[1 23 4 567]
[3,33]
{2 3 4}
{ {} {1} }
[ {} {1} {2} ]
[{},{1},{2}]
{3:2}
{<<hello>>:'world", <<who>>:333}
{{}:{}[2]:7}
<<true>>+true
<<,,,>>
foo+blah
22+43/66.+[]
x+y@[2,2]+z@pos'''.split('\n'), []
