# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import string

def pidgin_terms():
    '''Test subset of pidgin for literal declarations.'''
    letters = string.ascii_lowercase + string.ascii_uppercase
    g = Grammar('expr')
    g.addRule('expr', [N('atom')], [N('ident'), T('!'), N('atom')])
    g.addRule('atom', [N('ident')], [N('str_lit')], [N('set')], [N('map')], [N('order')], [T('('),N('expr'),T(')')])
    g.addRule('set',   [T('{'), N('elem_lst',m='optional'), T('}')])
    g.addRule('order', [T('['), N('elem_lst',m='optional'), T(']')])
    g.addRule('map',   [T('{'), N('elem_kv',m='some'), T('}')],
                       [T('{'), T(':'), T('}')])
    g.addRule('elem_kv',  [N('expr'), T(':'), N('expr'), T(',',m='optional')])
    g.addRule('elem_lst', [N('repeat_elem',m='any'), N('final_elem')])
    g.addRule('repeat_elem', [N('expr'),T(',',m='optional')])
    g.addRule('final_elem', [N('expr')])
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
{'expr":{[N!'atom"][N!'binop1"]}}'''.split('\n'),\
'''
[)
][
[}
{]
{'a":}
'''.split('\n')
