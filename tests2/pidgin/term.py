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
    g.addRule('set', [T('{'), T('}')],
                     [T('{'), N('order_pair', m='any'), N('expr'), T(',',m='optional'), T('}')],
                     [T('{'), N('expr'), N('expr', m='some'), T('}')])
    g.addRule('order', [T('['), T(']')],
                       [T('['), N('order_pair', m='any'), N('expr'), T(',',m='optional'), T(']')],
                       [T('['), N('expr'), N('expr', m='some'), T(']')])
    g.addRule('order_pair', [N('expr'), T(',')])
    g.addRule('map',   [T('{'), T(':'), T('}')],
                       [T('{'), N('kv_comma',m='any'), N('expr'), T(':'), N('expr'), T(',',m='optional'), T('}')],
                       [T('{'), N('kv_pair'), N('kv_pair',m='some'), T('}')])
    g.addRule('kv_pair',  [N('expr'), T(':'), N('expr')])
    g.addRule('kv_comma', [N('expr'), T(':'), N('expr'), T(',')])
    g.addRule('str_lit', [T("'"), Glue(), S(['"'],True,m='any'), T('"'), Remove()],
                         [T('<<'), Glue(), N('str_lit2',m='any'), T('>>'), Remove()])
    g.addRule('str_lit2', [S([">"],True)], [T('>'), S([">"],True)])
    g.addRule('ident', [S(list(letters)+['_']), Glue(), S(list(letters+string.digits)+['_'], m='any'), Remove()])

    return g, \
'''[]
{}
{:}
'hello"
<<hello>>
X!Y
X!'world"
X!<<world>>
['a" 'b" <<c>>]
['a"  'b"'c"]
[x y12  z14 w]
[x, y12,z14,  w]
[x, y12,z14,  w,]
{'a"'b"'c"}
{'a" 'b"  'c"}
{'a", 'b",  'c"}
{'a", 'b",  'c",}
{'a":'"'b":'"'c":<<>>}
{'a":[X!'a"]'b":[X!'b"]'c":[]}
{'a":[X!'a"], 'b":[X!'b"], 'c":[]}
{'name":{[N!'a"][T!'b"]}}
{'name":{[N!'a"][T!'a",T!'b",T!'c"]}}
{'expr":{[N!'atom"][N!'binop1"]}}'''.split('\n'),\
'''
[)
][
[}
{]
{x y12,  z14 w}
{x, y12 z14,  w}
[x y12,  z14 w]
[x, y12 z14,  w]
{'a":[X!'a"],'b":[X!'b"]'c":[]}
{'a":[X!'a"],,'b":[X!'b"],'c":[]}
{'a":[X!'a"] 'b":[X!'b"] 'c":[],}
{'a":}
'''.split('\n')

def pidgin_term2():
    '''Test subset of pidgin for literal declarations.'''
    letters = string.ascii_lowercase + string.ascii_uppercase
    g = Grammar('expr')
    g.setDiscard(S(' \t\r\n',m='some'))
    g.addRule('expr', [N('atom')], [N('ident'), T('!'), N('atom')])
    g.addRule('atom', [N('ident')], [N('str_lit')], [N('set')], [N('map')], [N('order')], [T('('),N('expr'),T(')')])
    g.addRule('set', [T('{'), T('}')],
                     [T('{'), N('order_pair', m='any'), N('expr'), T(',',m='optional'), T('}')],
                     [T('{'), N('expr'), N('expr', m='some'), T('}')])
    g.addRule('order', [T('['), T(']')],
                       [T('['), N('order_pair', m='any'), N('expr'), T(',',m='optional'), T(']')],
                       [T('['), N('expr'), N('expr', m='some'), T(']')])
    g.addRule('order_pair', [N('expr'), T(',')])
    g.addRule('map',   [T('{'), T(':'), T('}')],
                       [T('{'), N('kv_comma',m='any'), N('expr'), T(':'), N('expr'), T(',',m='optional'), T('}')],
                       [T('{'), N('kv_pair'), N('kv_pair',m='some'), T('}')])
    g.addRule('kv_pair',  [N('expr'), T(':'), N('expr')])
    g.addRule('kv_comma', [N('expr'), T(':'), N('expr'), T(',')])
    g.addRule('str_lit', [T("'"), Glue(), S(['"'],True,m='any'), T('"'), Remove()],
                         [T('u('), Glue(), S([')'],True,m='any'), T(')'), Remove()])
    g.addRule('ident', [S(list(letters)+['_']), Glue(), S(list(letters+string.digits)+['_'], m='any'), Remove()])

    return g, \
'''{'str_lit": { [T!u('), G!'", TAN!{u(")}, T!u(")] [T!'u(", G!'", TAN!{')"},  T!')"] }}'''.split('\n'), []


working='''
Execute s0 { s2 expr s23 : s67 { s2 [ s3 expr s40 ( s4 ' s61 ) s61 , s61   s61 G s61 ! s61 ' s61 " s235 at 27
Handle match on old s0 { s2 expr s23 : s67 { s2 [ s3 expr s40 ( s4 ' s61 ) s61 , s61   s61 G s61 ! s61 ' s61 " s235
                 => s0 { s2 expr s23 : s67 { s2 [ s3 expr s40 ( s4 str_lit
Execute s0 { s2 expr s23 : s67 { s2 [ s3 order_pair s47 ident s8 ! s63 ' s61 at 26
Execute s0 { s2 expr s23 : s67 { s2 [ s3 expr s40 ( s4 str_lit s13 at 27
Handle match on old s0 { s2 expr s23 : s67 { s2 [ s3 expr s40 ( s4 str_lit s13
'''
