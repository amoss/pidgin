# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import string

# TODO: where is the glue?
def quoted_str():
    '''Q: ' [^"]* " | u( [^)]* \)

       Test inverted character sets and glue.'''
    g = Grammar('Q')
    g.addRule('Q', [T("'"), S(['"'],True,m='any'), T('"')], [T('u('), S([')'],True,m='any'), T(')')])
    return g, ['\'"', 'u()', '\'x"', 'u(x)', '\'xx"', 'u(xx)', '\'xxx"', 'u(xxx)', '\'lol longer string"', 'u(lol longer string)'], \
           ['\'', 'u(', '"', ')', '\')', 'u("', '\'""', 'u())'], \
           []

def quoted_str2():
    '''Q: ' [^"]* " | << ([^>] | > [^>])* >>

       Test inverted character sets and glue, matching a two-symbol terminator.'''
    g = Grammar('Q')
    g.addRule('Q', [T("'"), Glue(), S(['"'],True,m='any'), T('"'), Remove()],
                   [T('<<'), Glue(), N('Qi',m='any'), T('>>'), Remove()])
    g.addRule('Qi', [S([">"],True)], [T('>'), S([">"],True)])
    return g, ['\'"',
               '\'\'"',
               '\'x"',
               '\'xx"',
               '\'xxx"',
               '\' xxx"',
               '\'xxx "',
               '\' xxx "',
               '\' <xxx "',
               '\' <<xxx>> "',
               '\'lol longer string"',
               '\'0123456789abcdefghijklmnopqrstuvwxyzöäå"',
               '<<>>',
               '<<<<>>',
               '<<x>>',
               '<<xx>>',
               '<<xxx>>',
               '<< xxx>>',
               '<<xxx >>',
               '<< xxx >>',
               '<< \'xxx >>',
               '<< \'xxx" >>',
               '<<lol longer string>>',
               '<<lol>longer>string>>',
               '<<0123456789abcdefghijklmnopqrstuvwxyzöäå>>'], \
              ['\'',
               '"',
               '\'""',
               '\'>>',
               '"\'',
               '<<',
               '>>',
               '<<>>>>',
               '<<"',
               '>><<',
               'x\'y"',
               'x<<y>>'], \
               []

def quoted_str3():
    '''Q: " ([^\"] | \\ [^] )* "

       Test C-style strings with two-symbol escape sequences.'''
    g = Grammar('Q')
    g.addRule('Q', [T('"'), Glue(), N('Qi',m='any'), T('"'), Remove()])
    g.addRule('Qi', [S(["\\",'"'],True)], [T('\\'), S([],True)])
    return g, ['""',
               '"\\\\"',
               '"hello world"',
               '"0123456789abcdefghijklmnopqrstuvwxyzöäå"',
               '"\\t\\\\\\n"',
               '"\\""',
               '"\\"hello world\\""'], \
              ['"',
               '"\\"'
               '"\\\\\\"',
               '"x"y',
               'x"y"'], \
               []

def quoted_str4():
    '''L: I  | I ! L | Q    Q: ' [^"]* " | u( [^)]* \)    I: [a-z] Glue [a-z0-9]* Remover

       Test pidgin-style strings in a language with a single binary operator.'''
    letters = string.ascii_lowercase + string.ascii_uppercase
    g = Grammar('L')
    g.addRule('L', [N("I")], [N("I"), T("!"), N("L")], [N("Q")])
    g.addRule('Q', [T("'"), S(['"'],True,m='any'), T('"')], [T('u('), S([')'],True,m='any'), T(')')])
    g.addRule('I', [S(list(letters)+['_']), Glue(), S(list(letters+string.digits)+['_'], m='any'), Remove()])
    return g, ['x', 'x2', 'T', '\'"', '\'xy"', '\'x y z"',
               'x!y', 'x!y2', 'x!\'"', 'x!\'y"', 'x!y!z', 'T!\'longer string"'], \
              ['', '2x', '\'"!\'"', 'T!""', 'T!\'\''], \
              []

def quoted_str5():
    '''Binop: I ! Binop | Atom   Atom: I | Q    Q: ' [^"]* " | u( [^)]* \)    I: [a-z] Glue [a-z0-9]* Remover

       Test pidgin-style strings in a language with a single binary operator. Differs to the previous
       case by splitting the ident and indent-plus-operator into separate rules to simulate a piece
       of the pidgin grammar.'''
    letters = string.ascii_lowercase + string.ascii_uppercase
    g = Grammar('Binop')
    g.addRule('Binop', [N("I"), T("!"), N("Atom")], [N("Atom")])
    g.addRule('Atom', [N("I")], [N("Q")])
    g.addRule('Q', [T("'"), S(['"'],True,m='any'), T('"')], [T('u('), S([')'],True,m='any'), T(')')])
    g.addRule('I', [S(list(letters)+['_']), Glue(), S(list(letters+string.digits)+['_'], m='any'), Remove()])
    return g, ['x', 'x2', 'T', '\'"', '\'xy"', '\'x y z"',
               'x!y', 'x!y2', 'x!\'"', 'x!\'y"', 'T!\'longer string"'], \
              ['', '2x', '\'"!\'"', 'T!""', 'T!\'\''], \
              []
