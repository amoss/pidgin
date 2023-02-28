# Copyright (C) 2003 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import html
from .graph import Graph
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
            if symbol is not None and not symbol.isTerminal():
                rule = self.grammar.rules[symbol.name]
                for clause in rule.clauses:
                    result.add(clause.get(0))
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
    '''A state of the parser (i.e. a stack and input position). In a convention GLR parser this would
       just be the stack, but we are building a fused lexer/parser that operates on a stream of characters
       instead of terminals.'''
    def __init__(self, stack, position):
        self.stack = stack
        self.position = position

    def shifts(self, input):
        result = []
        astate = self.stack[-1]
        for t,nextState in astate.byTerminal.items():
            match = t.match(input[self.position:])
            if match is not None:
                print(f"Shift {t} @ {self.position}")
                result.append(PState(self.stack + [Parser2.Terminal(match,t),nextState], self.position+len(match)))
        return result

    def reductions(self):
        result = []
        astate = self.stack[-1]
        for clause in astate.byClause:
            print(f"Check {strs(self.stack)} for reduction by {clause}")
            newStack = self.checkHandle(clause)
            if newStack is not None:
                print(f"Reduced to {newStack}")
                print(f"Reduced to {strs(newStack)}")
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


class Parser2:
    def __init__(self, grammar, discard=None):
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
        pstates = [PState([self.start], 0)]
        while len(pstates)>0:
            next = []
            for p in pstates:
                if not isinstance(p.stack[-1],AState):
                    if p.position==len(input) and len(p.stack)==2:
                        yield p.stack[1]
                else:
                    next.extend(p.reductions())
                    next.extend(p.shifts(input))
            pstates = next

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



#class Parser:
#    def __init__(self, graph, discard=None):
#        self.graph = graph
#        self.discard = discard
#
#    @staticmethod
#    def stateProps(state):
#        if len(state.input)>30:
#            result =  f'[shape=none,label=< <table border="0"><tr><td>{html.escape(state.input[:30])}...</td></tr><hr/>'
#        else:
#            result =  f'[shape=none,label=< <table border="0"><tr><td>{html.escape(state.input)}</td></tr><hr/>'
#        if len(state.node.labels)<5:
#            result += ''.join([f"<tr><td>{html.escape(str(x))}</td></tr>" for x in state.node.labels])
#        else:
#            result += f"<tr><td>{len(state.node.labels)} configs</td></tr>"
#        result += '<hr/><tr><td>' + " ".join([html.escape(str(x)) for x in state.stack]) + '</td></tr></table> >]';
#        return result
#
#    def parse(self, input, trace=None):
#        if trace:
#            print("digraph {", file=trace)
#            counter = 0
#            nodeNames = {}
#            for n in self.graph.nodes:
#                nodeNames[n] = f"s{counter}"
#                counter += 1
#        self.states = set()
#        initial = Parser.State(self.graph.start, input, ())
#        self.states.add(initial)
#        if trace:
#            print(f'n{id(initial)} {Parser.stateProps(initial)}', file=trace)
#        done = {}        ## Stratify sets by input length to avoid memory cost, i.e. iterate on all states of same input size in one batch
#        counter = 0
#        traceEdges = []
#
#        while len(self.states)>0:
#            next = set()
#            for s in self.states:
#                print(s.input, s.stack, s.node)
#                counter += 1
#                if s.terminating() and len(s.input)==0 and len(s.stack)==1:
#                    if trace:
#                        print(f"n{id(s)} [fillcolor=blue, style=filled];", file=trace)
#                    yield s.stack[0]
#                for edge in self.graph.findEdgeBySource(s.node):
#                    print(edge.label)
#                    if isinstance(edge.label, Clause):
#                        h = s.checkHandle(edge.label)
#                        print(h)
#                        if h is not None:
#                            ns = Parser.State(edge.target, s.input, h)
#                            if not ns in done:
#                                next.add(ns)
#                                done[ns] = ns
#                            else:
#                                ns = done[ns]   # Canonical instance of state
#                            if trace:
#                                print(f'n{id(ns)} {Parser.stateProps(ns)};', file=trace)
#                                print(f'n{id(s)} -> n{id(ns)} [label="reduce"];', file=trace)
#                    elif edge.label.isTerminal():
#                        m = edge.label.match(s.input)
#                        if m is not None:
#                            if len(m)==0:
#                                ns = Parser.State(edge.target, s.input, s.stack)
#                            else:
#                                remaining = s.input[len(m):]
#                                if not edge.label.sticky and self.discard is not None:
#                                    drop = self.discard.match(remaining)
#                                    if drop is not None and len(drop)>0:
#                                        remaining = remaining[len(drop):]
#                                ns = Parser.State(edge.target, remaining, s.stack + (edge.source,Parser.Terminal(m,edge.label)))
#                            if not ns in done:
#                                next.add(ns)
#                                done[ns] = ns
#                            else:
#                                ns = done[ns]   # Canonical instance of state
#                            if trace:
#                                print(f'n{id(ns)} {Parser.stateProps(ns)};', file=trace)
#                                print(f'n{id(s)} -> n{id(ns)} [label="shift"];', file=trace)
#                    else:
#                        if len(s.stack)>0 and s.stack[-1]==edge.label:
#                            ns = Parser.State(edge.target, s.input, s.stack)
#                            if not ns in done:
#                                next.add(ns)
#                                done[ns] = ns
#                            else:
#                                ns = done[ns]
#                            if trace:
#                                print(f'n{id(ns)} {Parser.stateProps(ns)};', file=trace)
#                                print(f'n{id(s)} -> n{id(ns)} [label="reduce"];', file=trace)
#
#            self.states = next
#        if trace:
#            print("}", file=trace)
#
#    class Terminal:
#        def __init__(self, chars, original, tag=None):
#            self.chars    = chars
#            self.tag      = tag
#            self.original = original
#
#        def __str__(self):
#            return self.chars
#
#        def __eq__(self, other):
#            return isinstance(other,Parser.Terminal) and self.chars==other.chars and self.tag==other.tag \
#                   and id(self.original)==id(other.original)
#
#        def __hash__(self):
#            return hash((self.chars,self.tag))
#
#        def matches(self, other):
#            return id(other)==id(self.original)
#
#        def dump(self, depth=0):
#            print(f"{'  '*depth}{self.chars}")
#
#    class Nonterminal:
#        def __init__(self, tag, children ):
#            self.tag      = tag
#            self.children = tuple(children)
#            for c in self.children:
#                assert isinstance(c,Parser.Terminal) or isinstance(c,Parser.Nonterminal), repr(c)
#
#        def __str__(self):
#            return self.tag
#
#        def __eq__(self, other):
#            return isinstance(other,Parser.Nonterminal) and self.tag==other.tag and self.children==other.children
#
#        def __hash__(self):
#            return hash(self.tag)
#
#        def matches(self, other):
#            if other.isTerminal():
#                return False
#            return self.tag == other.name
#
#        def dump(self, depth=0):
#            print(f"{'  '*depth}{self.tag}")
#            for c in self.children:
#                c.dump(depth+1)
#
#    class State:
#        def __init__(self, node, input, stack):
#            self.input = input
#            self.node  = node
#            self.stack = stack
#
#        def __eq__(self, other):
#            return self.input==other.input and self.node==other.node and self.stack==other.stack
#
#        def __hash__(self):
#            return hash((self.input, self.node, self.stack))
#
#        def terminating(self):
#            terminating = False
#            for config in self.node.labels:
#                if config.terminating:
#                    return True
#            return False
#
#        def checkHandle(self, clause):
#            '''Handles are as complex as regex in this system, and so the choice of greediness is very important.
#               It seems that greedy non-backtracking works on handles as long as we perform the match at the symbol
#               level, and not the character-level. For terminals each Parser.Terminal on the stack contains a
#               reference to the Grammar.Terminal it matched. For non-terminals we use the name.'''
#
#            def strs(iterable):
#                return " ".join([str(x) for x in iterable])
#            assert isinstance(clause, Clause), clause
#            s = len(self.stack) - 1
#            r = len(clause.rhs) - 1
#            hasMatched = False
#            while s >= 0:
#                if r<0:
#                    return self.stack[:s+1] + (Parser.Nonterminal(clause.lhs,self.stack[s+1:]),)
#                symbol = clause.rhs[r]
#                matching = self.stack[s].matches(symbol)
#                if not matching and hasMatched:
#                    r -= 1
#                    hasMatched = False
#                    continue
#                if not matching and symbol.modifier in ("just","some"):
#                    #print(f"checkHandle fail1 on {s} {r} {clause.lhs} <- {strs(self.stack)} vs {strs(clause.rhs)}")
#                    return None
#                if not matching and symbol.modifier in ("any","optional"):
#                    r -= 1
#                    hasMatched = False
#                if matching and symbol.modifier in ("just","optional"):
#                    s -= 1
#                    r -= 1
#                    hasMatched = False
#                if matching and symbol.modifier in ("any","some"):
#                    s -= 1
#                    hasMatched = True
#            if hasMatched and r==0:
#                r -= 1
#            if r<0:
#                return self.stack[:s+1] + (Parser.Nonterminal(clause.lhs,self.stack[s+1:]),)
#            #print(f"checkHandle fail2 on {clause.lhs} <- {self.stack}")
#            return None
