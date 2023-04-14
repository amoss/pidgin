# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

def quoted_str():
    '''Q: ' [^"]* " | u( [^)]* \)

       Test inverted character sets and glue.'''
    g = Grammar('Q')
    g.addRule('Q', [T("'"), S(['"'],True,m='any'), T('"')], [T('u('), S([')'],True,m='any'), T(')')])
    return g, ['\'"', 'u()', '\'x"', 'u(x)', '\'xx"', 'u(xx)', '\'xxx"', 'u(xxx)', '\'lol longer string"', 'u(lol longer string)'], \
           ['\'', 'u(', '"', ')', '\')', 'u("', '\'""', 'u())']

