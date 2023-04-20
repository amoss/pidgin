# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import string

def pidgin_term():
    '''Test subset of pidgin for literal declarations.'''
    letters = string.ascii_lowercase + string.ascii_uppercase
    g = Grammar('expr')
    g.setDiscard(S(' \t\r\n',m='some'))
    g.addRule('expr', [N('atom')], [N('ident'), T('!'), N('atom')])
    g.addRule('atom', [N('ident')], [N('str_lit')], [N('set')], [N('map')], [N('order')], [T('('),N('expr'),T(')')])
    g.addRule('set',   [T('{'), N('elem_lst',m='optional'), T('}')])
    g.addRule('order', [T('['), T(']')],
                       [T('['), N('order_pair', m='any'), N('expr'), T(',',m='optional'), T(']')],
                       [T('['), N('expr'), N('expr', m='some'), T(']')])
    g.addRule('order_pair', [N('expr'), T(',')])
    g.addRule('map',   [T('{'), N('elem_kv',m='some'), T('}')],
                       [T('{'), T(':'), T('}')])
    g.addRule('elem_kv',  [N('expr'), T(':'), N('expr'), T(',',m='optional')])
    g.addRule('elem_lst', [N('repeat_elem',m='any'), N('final_elem')])
    g.addRule('repeat_elem', [N('expr'), Glue(), S(', \r\t\n') ])
    g.addRule('final_elem',  [N('expr'), Glue(), S(', \r\t\n',m='optional'), Remove()])
    g.addRule('str_lit', [T("'"), Glue(), S(['"'],True,m='any'), Glue(), T('"')], 
                         [T('u('), Glue(), S([')'],True,m='any'), Glue(), T(')')])
    g.addRule('ident', [S(list(letters)+['_']), Glue(), S(list(letters+string.digits)+['_'], m='any'), Remove()])

    return g, \
'''[]
{}
{:}
'hello"
X!Y
X!'world"
['a"  'b"'c"]
[x y12  z14 w]
[x, y12,z14,  w]
[x, y12,z14,  w,]
{'a"'b"'c"}
{'a":'"'b":'"'c":'"}
{'a":[X!'a"]'b":[X!'b"]'c":[]}
{'name":{[N!'a"][T!'b"]}}
{'name":{[N!'a"][T!'a",T!'b",T!'c"]}}
{'expr":{[N!'atom"][N!'binop1"]}}'''.split('\n'),\
'''
[)
][
[}
{]
[x y12,  z14 w]
[x, y12 z14,  w]
{'a":}
'''.split('\n')
