# Copyright (C) 2003 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import html
from .grammar import Grammar, Clause
from .util import OrdSet, strs

class AState:
    '''A state in the LR(0) automaton'''
    def __init__(self, grammar, configs):
        self.grammar = grammar
        self.configurations = self.epsilonClosure(configs)
        self.byTerminal = {}
        self.byNonterminal = {}
        self.byClause = set()

    def __eq__(self, other):
        return isinstance(other,AState) and self.configurations==other.configurations

    def __hash__(self):
        return hash(self.configurations)

    def epsilonClosure(self, configs):
        result = OrdSet(configs)
        for c in result:
            symbol = c.next()
            if symbol is None: continue
            if not symbol.isTerminal():
                rule = self.grammar.rules[symbol.name]
                for clause in rule.clauses:
                    result.add(clause.get(0))
            if symbol.modifier in ("optional","any"):
                result.add(c.succ())
        return frozenset(result.set)

    def connect(self, symbol, next):
        assert isinstance(symbol,Grammar.Terminal) or isinstance(symbol,Grammar.Nonterminal), symbol
        assert isinstance(next,AState), next
        if symbol.isTerminal():
            self.byTerminal[symbol] = next
        else:
            self.byNonterminal[symbol.name] = next

    def addReducer(self, clause):
        self.byClause.add(clause)

class PState:
    counter = 1
    '''A state of the parser (i.e. a stack and input position). In a convention GLR parser this would
       just be the stack, but we are building a fused lexer/parser that operates on a stream of characters
       instead of terminals.'''
    def __init__(self, stack, position):
        self.stack = stack
        self.position = position
        self.id = PState.counter
        PState.counter += 1

    def shifts(self, input):
        result = []
        astate = self.stack[-1]
        for t,nextState in astate.byTerminal.items():
            match = t.match(input[self.position:])
            if match is not None:
                result.append(PState(self.stack + [Parser2.Terminal(match,t),nextState], self.position+len(match)))
        return result

    def reductions(self):
        result = []
        astate = self.stack[-1]
        for clause in astate.byClause:
            newStack = self.checkHandle(clause)
            if newStack is not None:
                result.append(PState(newStack, self.position))
        return result

    def checkHandle(self, clause):
        '''Handles are as complex as regex in this system, and so the choice of greediness is very important.
           It seems that greedy non-backtracking works on handles as long as we perform the match at the symbol
           level, and not the character-level. For terminals each Parser.Terminal on the stack contains a
           reference to the Grammar.Terminal it matched. For non-terminals we use the name.'''
        assert isinstance(clause, Clause), clause
        s = len(self.stack) - 1         # Track index of state above symbol being checked
        r = len(clause.rhs) - 1         # Track index of symbol being checked
        hasMatched = False
        while s >= 1:
            def prepare():
                preHandle = self.stack[:s+1]
                preHandle.append(Parser2.Nonterminal(clause.lhs,()))
                if clause.lhs is not None:
                    preHandle.append(preHandle[-2].byNonterminal[clause.lhs])
                return preHandle

            if r<0:
                return prepare()
            symbol = clause.rhs[r]
            matching = self.stack[s-1].matches(symbol)
            if not matching and hasMatched:
                r -= 1
                hasMatched = False
                continue
            if not matching and symbol.modifier in ("just","some"):
                #print(f"checkHandle fail1 on {s} {r} {clause.lhs} <- {strs(self.stack)} vs {strs(clause.rhs)}")
                return None
            if not matching and symbol.modifier in ("any","optional"):
                r -= 1
                hasMatched = False
            if matching and symbol.modifier in ("just","optional"):
                s -= 2
                r -= 1
                hasMatched = False
            if matching and symbol.modifier in ("any","some"):
                s -= 2
                hasMatched = True
        if hasMatched and r==0:
            r -= 1
        if r<0:
            return prepare()
        #print(f"checkHandle fail2 on {clause.lhs} <- {self.stack}")
        return None

    def dotLabel(self, input):
        remaining = input[self.position:]
        astate = self.stack[-1]
        if not isinstance(astate,AState):
            return "<Success>"
        if len(remaining)>30:
            result =  f'< <table border="0"><tr><td>{html.escape(remaining[:30])}...</td></tr><hr/>'
        else:
            result =  f'< <table border="0"><tr><td>{html.escape(remaining)}</td></tr><hr/>'

        if len(astate.configurations)>5:
            result += f"<tr><td>{len(astate.configurations)} configs</td></tr>"
        else:
            result += ''.join([f"<tr><td>{html.escape(str(c))}</td></tr>" for c in astate.configurations])

        onlySymbols = [ s for s in self.stack if not isinstance(s,AState) ]
        if len(onlySymbols)>5:
            result += '<hr/><tr><td>... ' + " ".join([html.escape(str(s)) for s in onlySymbols[-5:]]) + '</td></tr></table> >';
        else:
            result += '<hr/><tr><td>' + " ".join([html.escape(str(s)) for s in onlySymbols]) + '</td></tr></table> >';
        return result



class Parser2:
    def __init__(self, grammar, discard=None, trace=None):
        self.grammar = grammar
        self.discard = discard
        entry = Clause(None, [Grammar.Nonterminal(grammar.start)], terminating=True)
        initial = AState(grammar, [entry.get(0)])
        self.start = initial
        worklist = OrdSet([initial])

        for state in worklist:
            nextSymbols = set( config.next() for config in state.configurations)
            reducing = None in nextSymbols
            nextSymbols.discard(None)
            for symbol in nextSymbols:
                possibleConfigs = [ c.succ() for c in state.configurations if c.next()==symbol ]
                next = AState(grammar, possibleConfigs)
                next = worklist.add(next)
                state.connect(symbol, next)
                #if symbol.modifier in ("any","some"):
                #    state.connect(symbol, state)
            if reducing:
                reducingConfigs = [ c for c in state.configurations if c.next() is None ]
                for r in reducingConfigs:
                    state.addReducer(r.clause)

        self.states = worklist.set
        assert isinstance(self.states, dict)

    def dotAutomaton(self, output):
        print("digraph {", file=output)
        for s in self.states:
            label = "\\n".join([str(c).replace('"','\\"') for c in s.configurations])
            if len(s.byClause)>0:
                print(f's{id(s)} [label="{label}",shape=rect];', file=output)
            else:
                print(f's{id(s)} [label="{label}"];', file=output)
            for t,next in s.byTerminal.items():
                label = str(t).replace('"','\\"')
                print(f's{id(s)} -> s{id(next)} [label="{label}"];', file=output)
            for name,next in s.byNonterminal.items():
                print(f's{id(s)} -> s{id(next)} [label="NT({name})"];', file=output)
        print("}", file=output)

    def parse(self, input, trace=None):
        if trace is not None:                    print("digraph {\nrankdir=LR;", file=trace)
        pstates = [PState([self.start], 0)]
        while len(pstates)>0:
            next = []
            for p in pstates:
                if trace is not None:            print(f"s{p.id} [shape=none,label={p.dotLabel(input)}];", file=trace)
                if not isinstance(p.stack[-1],AState):
                    if p.position==len(input) and len(p.stack)==2:
                        yield p.stack[1]
                        if trace is not None:    print(f"s{p.id} [shape=rect,label={p.dotLabel(input)}];", file=trace)
                else:
                    reduces = p.reductions()
                    shifts  = p.shifts(input)
                    next.extend(reduces)
                    next.extend(shifts)
                    if trace is not None:
                        for r in reduces:
                            print(f's{p.id} -> s{r.id} [label="reduce"];', file=trace)
                        for s in shifts:
                            print(f's{p.id} -> s{s.id} [label="shift"];', file=trace)
            pstates = next
        if trace is not None: print("}", file=trace)

    class Terminal:
        def __init__(self, chars, original):
            self.chars    = chars
            self.original = original

        def __str__(self):
            return self.chars

        def matches(self, other):
            return id(other)==id(self.original)

        def dump(self, depth=0):
            print(f"{'  '*depth}{self.chars}")

    class Nonterminal:
        def __init__(self, tag, children ):
            self.tag      = tag
            self.children = tuple(children)
            for c in self.children:
                assert isinstance(c,Parser.Terminal) or isinstance(c,Parser.Nonterminal), repr(c)

        def __str__(self):
            return str(self.tag)

        def matches(self, other):
            if other.isTerminal():
                return False
            return self.tag == other.name

        def dump(self, depth=0):
            print(f"{'  '*depth}{self.tag}")
            for c in self.children:
                c.dump(depth+1)
