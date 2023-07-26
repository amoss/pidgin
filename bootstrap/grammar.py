# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from functools import total_ordering
from .util import strs


class Rule:
    '''The collection of clauses that define a production in the grammar.'''
    def __init__(self, name, grammar):
        self.name = name
        self.grammar = grammar
        self.clauses = set()

    def add(self, initialBody):
        body = [ symbol for symbol in initialBody ]
        self.clauses.add( Clause(self.name, body) )


@total_ordering
class Clause:
    '''A sentence of symbols that forms a r.h.s of a production rule. Each clause
       is a non-prioritized choice of symbols.'''
    def __init__(self, name, body, terminating=False):
        self.lhs = name
        self.rhs = body
        for i,symbol in enumerate(self.rhs):
            if isinstance(symbol, Grammar.Glue):
                symbol.within = self
                symbol.position = i
        self.terminating = terminating
        self.configs = [None] * (len(body)+1)

    def __str__(self):
        return f"{self.lhs} <- {' '.join([str(x) for x in self.rhs])}"

    def __lt__(self, other):
        return self.rhs[0].order() < other.rhs[0].order()


class Grammar:
    '''The collection of rules that define a language.'''
    def __init__(self, start):
        self.rules    = dict()
        self.start    = start
        self.discard  = None

    def addRule(self, name, *body):
        assert not name in self.rules.keys()
        rule = Rule(name, self)
        for b in body:
            rule.add(b)
        self.rules[name] = rule
        return rule

    def setDiscard(self, terminal):
        self.discard = terminal

    def dump(self):
        for rule in self.rules.values():
            print(f"{rule.name}:")
            for clause in rule.clauses:
                print(f"  {strs(clause.rhs)}")

    class TermString:
        def __init__(self, match, modifier="just", tag='', original=None):
            '''A terminal symbol with a *modifier* that matches a string literal *match*.'''
            self.string = match
            self.tag = tag
            assert modifier in ("any","just","some","optional"), modifier
            self.modifier = modifier
            self.strength = 'greedy'
            self.original = self if original is None else original
            self.isTerminal    = True
            self.isNonterminal = False

        def __str__(self):
            tag = f",{self.tag}" if self.tag!="" else ""
            return f"T({repr(self.string)},{self.modifier}{tag})"


    class TermSet:
        def __init__(self, charset, modifier="just", inverse=False, tag='', original=None):
            '''A terminal symbol with a *modifier* that matches a set of characters. These work
               the same as character-classes in regex and allow an *inverse* match. The *tag*
               is an opaque value that can be recovered from the parse-tree node.'''
            assert modifier in ("any","just","some","optional"), modifier
            self.modifier = modifier
            self.strength = "greedy"
            self.chars = frozenset(charset)
            self.inverse  = inverse
            self.tag      = tag
            self.original = self if original is None else original
            self.isTerminal    = True
            self.isNonterminal = False

        def __str__(self):
            if len(self.chars)<=5:
                charset = "".join([c for c in self.chars])
            else:
                charset = "".join([c for c in list(self.chars)[:5]]) + f' +{len(self.chars)-5}'
            if self.inverse:
                result = 'T(^{' + charset + '}'
            else:
                result = 'T({' + charset + '}'
            tag = f",{self.tag}" if self.tag!="" else ""
            return f'{result},{self.modifier}{tag})'


    class Nonterminal:
        def __init__(self, name, strength="greedy", modifier="just"):
            '''A non-terminal symbol in the grammar. Equality is over *name*.'''
            assert modifier in ("any", "just", "some", "optional"), modifier
            assert strength in ("all", "frugal", "greedy"), strength
            self.name     = name
            self.modifier = modifier
            self.strength = strength
            self.isTerminal    = False
            self.isNonterminal = True

        def copy(self):
            return Grammar.Nonterminal(self.name, strength=self.strength, modifier=self.modifier)

        def __str__(self):
            return f"N({self.strength},{self.modifier},{self.name})"

    class Glue:
        def __init__(self):
            '''Glue is a special-symbol that disables the discard channel (gluing together symbols
               without spacing.'''
            self.within = None
            self.position = None
            self.modifier = "just"
            self.strength = "greedy"
            self.isTerminal    = False
            self.isNonterminal = False

        def __str__(self):
            return "Glue"

    class Remover:
        def __init__(self):
            '''Remover is a special-symbol that enables the discard channel (removing the effect of Glue).'''
            self.within = None
            self.position = None
            self.modifier = "just"
            self.strength = "greedy"
            self.isTerminal    = False
            self.isNonterminal = False

        def __str__(self):
            return "Remover"

