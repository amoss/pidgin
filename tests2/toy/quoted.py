# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

def quoted_str():
    '''Q: ' [^"]* " | u( [^)]* \)

       Test inverted character sets and glue.'''
    g = Grammar('Q')
    g.addRule('Q', [T("'"), S(['"'],True,m='any'), T('"')], [T('u('), S([')'],True,m='any'), T(')')])
    return g, ['\'"', 'u()', '\'x"', 'u(x)', '\'xx"', 'u(xx)', '\'xxx"', 'u(xxx)', '\'lol longer string"', 'u(lol longer string)'], \
           ['\'', 'u(', '"', ')', '\')', 'u("', '\'""', 'u())']

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
               'x<<y>>']

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
               'x"y"']

