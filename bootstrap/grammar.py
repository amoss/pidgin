# Copyright (C) 2003 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from functools import total_ordering
from .graph import Graph

class OrdSet:
    def __init__(self):
        self.set = {}
        self.ord = []

    def add(self, v):
        if not v in self.set:
            self.set[v] = v
            self.ord.append(v)
        return self.set[v]

    def __len__(self):
        return len(self.set)

    def __contains__(self, v):
        return v in self.set

    def __iter__(self) :
        for x in self.ord:
            yield x

class Rule:
    def __init__(self, name):
        self.name = name
        self.clauses = set()

    def add(self, body):
        self.clauses.add( Clause(self.name, body) )


@total_ordering
class Clause:
    def __init__(self, name, body, terminating=False):
        self.lhs = name
        self.rhs = body
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
        self.succs = set()

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
        return self.clause.lhs==other.clause.lhs and self.position==other.position and self.clause.rhs==other.clause.rhs

    def __hash__(self):
        return hash((self.clause.lhs, str(self.clause.rhs), self.position))

class Grammar:
    def __init__(self, start):
        self.rules    = dict()
        self.start    = start
        self.worklist = OrdSet()
        self.discard  = None

    def addRule(self, name, initialClause):
        assert not name in self.rules.keys()
        rule = Rule(name)
        rule.add(initialClause)
        self.rules[name] = rule
        return rule

    def setDiscard(self, terminal):
        self.discard = terminal

    def build(self):
        result = Graph()
        self.entry = Clause("<outside>", [self.Nonterminal(self.start)], terminating=True)
        self.worklist = OrdSet()
        self.worklist.add(self.entry.get(0))
        nodes = {}

        for config in self.worklist:
            configNode = result.force(config)
            if config.position < len(config.clause.rhs):
                sym = config.clause.rhs[config.position]
                if isinstance(sym, self.Terminal):
                    succ = config.clause.get(config.position+1)
                    succNode = result.force(succ)
                    result.connect(configNode,succNode,sym) # "shift")
                    self.worklist.add(succ)
                    if sym.modifier in ("any","optional"):
                        result.connect(configNode, succNode, "predict")     # Match zero instancees
                    if sym.modifier in ("any","some"):
                        result.connect(configNode, configNode, sym) #  "shift")    # Back-edge for loop
                if isinstance(sym, self.Nonterminal):
                    rule = self.rules[sym.name]
                    ret = config.clause.get(config.position+1)
                    retNode = result.force(ret)
                    for clause in rule.clauses:
                        succ  = clause.get(0)
                        succNode = result.force(succ)
                        final = clause.get(len(clause.rhs))
                        finalNode = result.force(final)
                        result.connect(configNode, succNode, "predict")
                        result.connect(finalNode, retNode, clause) # "reduce")
                        self.worklist.add(succ)
                        self.worklist.add(final)
                        self.worklist.add(ret)
                        if sym.modifier in ("any","optional"):
                            result.connect(configNode, retNode, "predict")     # Match zero instancees
                        if sym.modifier in ("any","some"):
                            result.connect(finalNode, configNode, clause) # "reduce")    # Back-edge for loop
            else:
                pass # config was created as a final so already has reduce edge
        result.start = result.force(self.entry.get(0))

        while True:
            it = result.findEdgeByLabel("predict")
            first = next(it,None)
            if first is None:
              break
            result.fold(first)
        return result

    class Terminal:
        def __init__(self, match, modifier="just", inverse=False, sticky=False):
            assert modifier in ["any", "just", "some", "optional"]
            if isinstance(match, str):
                self.string = match
                self.chars  = None
            else:
                self.chars  = frozenset(match)
                self.string = None
            self.modifier = modifier
            self.inverse  = inverse
            self.sticky   = sticky

        def __str__(self):
            if self.string is not None:
                return f"T({self.modifier},{self.string})"
            return f"T({self.modifier},{self.chars})"

        def order(self):
            if self.chars is not None:
                return (0, 0, self.chars)
            return (0, 1, self.string)

        def __eq__(self, other):
            return isinstance(other,Grammar.Terminal) \
               and self.string==other.string \
               and self.chars==other.chars \
               and self.modifier==other.modifier \
               and self.inverse==other.inverse

        def __hash__(self):
            return hash((self.string,self.chars))

        def isTerminal(self):
            return True

        def match(self, input):
            allowzero = self.modifier in ("any","optional")
            limit = len(input) if self.modifier in ("any","some") else 1
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
            return Grammar.Terminal(self.string if self.chars is None else self.chars, "just", self.inverse)

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

        def isTerminal(self):
            return False

        def exactlyOne(self):
            return Grammar.Nonterminal(self.name, "just")

