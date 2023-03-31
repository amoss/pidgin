# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from functools import total_ordering
from .util import strs

class Rule:
    def __init__(self, name, grammar):
        self.name = name
        self.grammar = grammar
        self.clauses = set()

    def add(self, initialBody):
        body = [ self.grammar.canonical(symbol) if symbol.isTerminal() else symbol
                 for symbol in initialBody]
        self.clauses.add( Clause(self.name, body) )


@total_ordering
class Clause:
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

    def isTerminal(self):
        return False

    def get(self, position):
        if self.configs[position] is None:
            self.configs[position] = Configuration(self, position)
        return self.configs[position]

class Configuration:
    def __init__(self, clause, position):
        self.clause = clause
        assert -1 <= position and position <= len(self.clause.rhs)
        self.terminating = clause.terminating and (position==len(self.clause.rhs))
        self.position = position

    def __str__(self):
        result = f"{self.clause.lhs} <- "
        for i,s in enumerate(self.clause.rhs):
            if i==self.position:
                result += "*"
            result += str(s)
        if self.position==len(self.clause.rhs):
            result += "*"
        return result

    def __eq__(self, other):
        if not isinstance(other,Configuration):
            return False
        return self.clause.lhs==other.clause.lhs and self.position==other.position and\
               self.clause.rhs==other.clause.rhs

    def __hash__(self):
        return hash((self.clause.lhs, str(self.clause.rhs), self.position))

    def next(self):
        if self.position==len(self.clause.rhs):
            return None
        return self.clause.rhs[self.position]

    def succ(self):
        assert self.position < len(self.clause.rhs)
        return Configuration(self.clause, self.position+1)

class Grammar:
    def __init__(self, start):
        self.rules    = dict()
        self.start    = start
        self.discard  = None
        self.canonicalTerminals = dict()

    def canonical(self, terminal):
        assert terminal.isTerminal(), terminal
        if not terminal in self.canonicalTerminals:
            self.canonicalTerminals[terminal] = terminal
        return self.canonicalTerminals[terminal]

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
        def __init__(self, match, modifier="just", tag=''):
            '''A terminal symbol that matches a string literal *match*. If the *modifier* is repeating then
               the match is always greedy. If non-greedy matching is required then it can be simulated by
               wrapping in a non-terminal (with glue if appropriate).'''
            self.string = match
            self.tag = tag
            assert modifier in ("any","just","some","optional"), modifier
            self.modifier = modifier

        def __str__(self):
            tag = f",{self.tag}" if self.tag!="" else ""
            return f"T({repr(self.string)},{self.modifier}{tag})"

        def sig(self):
            return (self.match, self.tag, self.modifier)

        def __eq__(self,other):
            return isinstance(other,Grammar.TermString) and self.sig()==other.sig()

        def __hash__(self):
            return hash(self.sig())

        def isTerminal(self):
            return True

        def match(self, input):
            limit = len(input) if self.modifier in ("any","some") else 1
            i = 0
            n = len(self.string)
            original = input[:]
            #print(f"Matching {i} {n} {self.string} {input}")
            while i<limit and input[:n]==self.string:
                i += 1
                input = input[n:]
                #print(f"Matching {i} {n} {self.string} {input}")
            if i>0:
                return original[:i*n]

        def exactlyOne(self):
            return Grammar.TermString(self.string, modifier="just", tag=self.tag)

        # Does this still get used or is it dead?
        #def order(self):
        #    return (0, 1, self.string)

    class TermSet:
        def __init__(self, charset, modifier="just", inverse=False, tag=''):
            '''The *modifier* applies to matching the *charset* within a single symbol, in contrast
               to how the modifier works on non-terminals.'''
            assert modifier in ("any","just","some","optional"), modifier
            self.internal = "some" if modifier in ("any","some") else "just"
            self.modifier = "optional" if modifier in ("optional","any") else "just"
            self.orig = modifier
            self.chars = frozenset(charset)
            self.inverse  = inverse
            self.tag      = tag

        def __str__(self):
            if len(self.chars)<=5:
                charset = ",".join([c if c!=',' else "','" for c in self.chars])
            else:
                charset = ",".join([c if c!=',' else "','" for c in list(self.chars)[:5]]) + f' +{len(self.chars)-5}'
            if self.inverse:
                result = 'T(^{"' + charset + '},'
            else:
                result = 'T({"' + charset + '},'
            tag = f",{self.tag}" if self.tag!="" else ""
            return f'{result},{self.orig}{tag})'

        def sig(self):
            return (self.chars, self.modifier, self.inverse, self.tag)

        def __eq__(self,other):
            return isinstance(other,Grammar.TermSet) and self.sig()==other.sig()

        def __hash__(self):
            return hash(self.sig())

        def isTerminal(self):
            return True

        def exactlyOne(self):
            return Grammar.TermSet(self.chars, modifier="just", inverse=self.inverse, tag=self.tag)

        # Does this still get used or is it dead?
        #def order(self):
        #    return (0,0,self.chars)

        def match(self, input):
            limit = len(input) if self.internal in ("any","some") else 1
            i = 0
            while i<limit and i<len(input) and ((input[i] not in self.chars) == self.inverse):
                i += 1
            if i>0:
                return input[:i]


    class Nonterminal:
        def __init__(self, name, strength="greedy", modifier="just"):
            assert modifier in ("any", "just", "some", "optional"), modifier
            assert strength in ("all", "frugal", "greedy"), strength
            self.name     = name
            self.modifier = modifier
            self.strength = strength

        def __str__(self):
            return f"N({self.strength},{self.modifier},{self.name})"

        # Does this still get used or is it dead?
        #def order(self):
        #    return (1, 0, self.name)

        def sig(self):
            return (self.name, self.modifier)

        def __eq__(self, other):
            return isinstance(other,Grammar.Nonterminal) and self.sig()==other.sig()

        def __hash__(self):
            return hash(self.sig())

        def isTerminal(self):
            return False

        def exactlyOne(self):
            return Grammar.Nonterminal(self.name, strength=self.strength, modifier="just")

    class Glue:
        def __init__(self):
            self.within = None
            self.position = None
            self.modifier = "just"

        def __str__(self):
            return "Glue"

        def __eq__(self, other):
            return isinstance(other,Grammar.Glue) and self.within==other.within and self.position==other.position

        def __hash__(self):
            return hash((1,self.within,self.position))

        def isTerminal(self):
            return False

    class Remover:
        def __init__(self):
            self.within = None
            self.position = None
            self.modifier = "just"

        def __str__(self):
            return "Remover"

        def __eq__(self, other):
            return isinstance(other,Grammar.Remover) and self.within==other.within and self.position==other.position

        def __hash__(self):
            return hash((2,self.within,self.position))

        def isTerminal(self):
            return False
