# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import string

def toy_ambiguous1():
    '''L: x | x L*

    Test a simple way to provoke ambiguity - list of xs can reduced by iteration or recursion.
    '''
    g = Grammar("L")
    g.addRule('L', [T("x")], [T("x"), N("L", m='any')])

    return g, ['x', 'xx'], \
              [''], \
              ['xxx', 'xxxx', 'xxxxx']


def toy_ambiguous2():
    '''L: x | L + L

    Test ambiguity with an operator that has neither precedence nor associativity.
    '''
    g = Grammar("L")
    g.addRule('L', [T("x")], [N("L"), T("+"), N("L")])

    return g, ['x', 'x+x'], \
              ['x+','+x','x++x','x+xx+x','x++x+x'], \
              ['x+x+x', 'x+x+x+x', 'x+x+x+x+x']

