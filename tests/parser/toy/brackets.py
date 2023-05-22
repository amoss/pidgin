# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import string

def toy_brackets1():
    '''L: P+   P: ( P* )

       Cleanest expression of the brackets language in the grammar.
    '''
    g = Grammar("L")
    g.addRule('L', [N("P", m="some")])
    g.addRule('P', [T("("), N("P", m="any"), T(")")])

    return g, ['()', '()()', '()()()', '(())', '(()())', '(()()())', '((())())'], \
              ['', '(', ')', '(()', ')(', '())', ')(('], \
              []


def toy_brackets2():
    '''L: P | P L   P: ( P* )

       Equivalent variation with explicit recursion on top rule, right-recursive form.
    '''
    g = Grammar("L")
    g.addRule('L', [N("P")], [N("P"), N("L")])
    g.addRule('P', [T("("), N("P", m="any"), T(")")])

    return g, ['()', '()()', '()()()', '(())', '(()())', '(()()())', '((())())'], \
              ['', '(', ')', '(()', ')(', '())', ')(('], \
              []


def toy_brackets3():
    '''L: P+   P: ( ) | ( L )

       Equivalent variation with explicit recursion on bottom rule, recursive form is bounded (framed).
    '''
    g = Grammar("L")
    g.addRule('L', [N("P", m="some")])
    g.addRule('P', [T("("), T(")")], [T("("), N("L"), T(")")])

    return g, ['()', '()()', '()()()', '(())', '(()())', '(()()())', '((())())'], \
              ['', '(', ')', '(()', ')(', '())', ')(('], \
              []


def toy_brackets4():
    '''L: L P | P   P: ( ) | ( L )

       Equivalent variation with explicit recursion on both rules, left-recursive form.
    '''
    g = Grammar("L")
    g.addRule('L', [N("L"), N("P")], [N("P")])
    g.addRule('P', [T("("), T(")")], [T("("), N("L"), T(")")])

    return g, ['()', '()()', '()()()', '(())', '(()())', '(()()())', '((())())'], \
              ['', '(', ')', '(()', ')(', '())', ')(('], \
              []


def toy_brackets5():
    '''L: L P | P   P: ( E* )

       Equivalent variation with explicit recursion on both rules, left-recursive form.
    '''
    g = Grammar("L")
    g.addRule('L', [N("L"), N("P")], [N("P")])
    g.addRule('P', [T("("), N("P", m="any"), T(")")])

    return g, ['()', '()()', '()()()', '(())', '(()())', '(()()())', '((())())'], \
              ['', '(', ')', '(()', ')(', '())', ')(('], \
              []


def toy_brackets6():
    '''L: P L | P   P: ( E* )

       Equivalent variation with explicit recursion on both rules, right-recursive form.
    '''
    g = Grammar("L")
    g.addRule('L', [N("P"), N("L")], [N("P")])
    g.addRule('P', [T("("), N("P", m="any"), T(")")])

    return g, ['()', '()()', '()()()', '(())', '(()())', '(()()())', '((())())'], \
              ['', '(', ')', '(()', ')(', '())', ')(('], \
              []

