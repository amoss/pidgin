# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from functools import total_ordering

class Rule:
    def __init__(self, name, grammar):
        self.name = name
        self.grammar = grammar
        self.clauses = set()

    def add(self, initialBody):
        body = [ self.grammar.canonical(symbol) if isinstance(symbol, Grammar.Terminal) else symbol
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
        assert isinstance(terminal, Grammar.Terminal), terminal
        if not terminal in self.canonicalTerminals:
            self.canonicalTerminals[terminal] = terminal
        return self.canonicalTerminals[terminal]

    def addRule(self, name, body):
        assert not name in self.rules.keys()
        rule = Rule(name, self)
        rule.add(body)
        self.rules[name] = rule
        return rule

    def setDiscard(self, terminal):
        self.discard = terminal


    class Terminal:
        def __init__(self, match, internal="just", external="just", inverse=False):
            '''The *internal* modifier is applied to matching character classes within the span of
               text that the Terminal matches. The *external* modifier is used to allow repetitions
               of the Terminal in the same manner as Nonterminals. Example:
                 Terminal("x","some") would match "x", "xx" ... -> T("x"), T("xx")...
                 Terminal("x","just","some") would match "x" -> T("x"), "xx" -> [T("x"),T("x")]...
               '''
            assert internal in ["just", "some"], internal
            assert external in ["any", "just", "some", "optional"], external
            if isinstance(match, str):
                self.string = match
                self.chars  = None
            else:
                self.chars  = frozenset(match)
                self.string = None
            self.internal = internal
            self.modifier = external
            self.inverse  = inverse

        def __str__(self):
            if self.string is not None:
                return f"T({self.modifier},{self.string})"
            if len(self.chars)<5:
                return f"T({self.modifier},{self.chars})"
            return f"T({self.modifier}, {len(self.chars)} elements)"

        def order(self):
            if self.chars is not None:
                return (0, 0, self.chars)
            return (0, 1, self.string)

        def __eq__(self, other):
            return isinstance(other,Grammar.Terminal) \
               and self.string==other.string \
               and self.chars==other.chars \
               and self.internal==other.internal \
               and self.modifier==other.modifier \
               and self.inverse==other.inverse

        def __hash__(self):
            return hash((self.string, self.chars, self.internal, self.modifier, self.inverse))

        def match(self, input):
            allowzero = self.internal in ("any","optional")
            limit = len(input) if self.internal in ("any","some") else 1
            if self.string is not None:
                i = 0
                n = len(self.string)
                original = input[:]
                #print(f"Matching {i} {n} {self.string} {input}")
                while i<limit and input[:n]==self.string:
                    i += 1
                    input = input[n:]
                    #print(f"Matching {i} {n} {self.string} {input}")
                if i==0:
                    return "" if allowzero else None
                return original[:i*n]
            if self.chars is not None:
                i = 0
                while i<limit and i<len(input) and ((input[i] not in self.chars) == self.inverse):
                    i += 1
                if i==0:
                    return "" if allowzero else None
                return input[:i]
            assert False

        def exactlyOne(self):
            return Grammar.Terminal(self.string if self.chars is None else self.chars, "just", inverse=self.inverse)

    class Nonterminal:
        def __init__(self, name, modifier="just"):
            assert modifier in ["any", "just", "some", "optional"]
            self.name = name
            self.modifier = modifier

        def __str__(self):
            return f"N({self.modifier},{self.name})"

        def order(self):
            return (1, 0, self.name)

        def __eq__(self, other):
            return isinstance(other,Grammar.Nonterminal) and self.name==other.name and self.modifier==other.modifier

        def __hash__(self):
            return hash((self.name, self.modifier))

        def exactlyOne(self):
            return Grammar.Nonterminal(self.name, "just")

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
            return hash((self.within,self.position))
