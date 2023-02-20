import html
from .graph import Graph
from .grammar import Grammar

def prefixesOf(s) :
    for i in range(1,len(s)+1):
        yield s[:i]


graph.dot(open("tree.dot","wt"))

class Parser:

    def __init__(self, graph):
        self.graph = graph

    @staticmethod
    def stateProps(state):
        result =  f'[shape=none,label=< <table border="0"><tr><td>{html.escape(state.input)}</td></tr><hr/>'
        result += ''.join([f"<tr><td>{html.escape(str(x))}</td></tr>" for x in state.node.labels])
        result += '<hr/><tr><td>' + " ".join([html.escape(str(x)) for x in state.stack]) + '</td></tr></table> >]';
        return result

    def parse(self, input, trace=None):
        if trace:
            print("digraph {", file=trace)
            counter = 0
            nodeNames = {}
            for n in self.graph.nodes:
                nodeNames[n] = f"s{counter}"
                counter += 1
        self.states = set()
        initial = Parser.State(self.graph.start, input, ())
        self.states.add(initial)
        if trace:
            print(f'n{id(initial)} {Parser.stateProps(initial)}', file=trace)
        done = set()        ## Stratify sets by input length to avoid memory cost, i.e. iterate on all states of same input size in one batch
        counter = 0
        traceEdges = []

        while len(self.states)>0:
            next = set()
            for s in self.states:
                #print(f"State: {s.input} :: {' '.join([str(x) for x in s.stack])}")
                counter += 1
                if s.terminating() and len(s.input)==0 and len(s.stack)==1:
                    if trace:
                        print(f"n{id(s)} [fillcolor=blue, style=filled];", file=trace)
                    print("Success!!!!")
                    s.stack[0].dump()
                for edge in self.graph.findEdgeBySource(s.node):
                    if edge.label.isTerminal():
                        m = edge.label.match(s.input)
                        if m is not None:
                            #print(f"  Shift {m} to {edge.target}")
                            ns = Parser.State(edge.target, s.input[len(m):], s.stack + (Parser.Terminal(m),))
                            next.add(ns)
                            if trace:
                                print(f'n{id(ns)} {Parser.stateProps(ns)}', file=trace)
                                traceEdges.append( (s,ns,"shift") )
                    else:
                        h = s.checkHandle(edge.label)
                        if h is not None:
                            #print(f"  Reduce by {edge.label} onto {' '.join([str(x) for x in h])}")
                            ns = Parser.State(edge.target, s.input, h)
                            next.add(ns)
                            if trace:
                                print(f'n{id(ns)} {Parser.stateProps(ns)}', file=trace)
                                traceEdges.append( (s,ns,"reduce") )

            done = done.union(self.states)
            next = next.difference(done)
            self.states = next
            print(f"Iteration with {len(next)} states")
        print(f"Processed {counter} states")
        if trace:
            for src,tar,lab in traceEdges:
                print(f'n{id(src)} -> n{id(tar)} [label="{lab}"];', file=trace)
            print("}", file=trace)

    class Terminal:
        def __init__(self, chars, tag=None):
            self.chars = chars
            self.tag = tag

        def __str__(self):
            return self.chars

        def matches(self, other):
            if not other.isTerminal():
                return False
            return other.match(self.chars)          # Ugly, use tags

        def dump(self, depth=0):
            print(f"{'  '*depth}{self.chars}")

    class Nonterminal:
        def __init__(self, tag, children):
            self.tag = tag
            self.children = tuple(children)
            for c in self.children:
                assert isinstance(c,Parser.Terminal) or isinstance(c,Parser.Nonterminal), repr(c)

        def __str__(self):
            return self.tag

        def matches(self, other):
            if other.isTerminal():
                return False
            return self.tag == other.name

        def dump(self, depth=0):
            print(f"{'  '*depth}{self.tag}")
            for c in self.children:
                c.dump(depth+1)

    class State:
        def __init__(self, node, input, stack):
            self.input = input
            self.node  = node
            self.stack = stack

        def __eq__(self, other):
            return self.input==other.input and self.node==other.node and self.stack==other.stack

        def __hash__(self):
            return hash((self.input, self.node, self.stack))

        def terminating(self):
            terminating = False
            for config in self.node.labels:
                if config.terminating:
                    return True
            return False

        def checkHandle(self, clause):
            '''Handles are as complex as regex in this system, treat variable-length modifiers as greedy and do not
               perform backtracking. This will cause failure cases (i.e. end of a clause is a repeating symbol and
               the same symbol/modifier is in the follows-set) but will do for now in order to investigate how this
               works out.'''
            s = len(self.stack) - 1
            r = len(clause.rhs) - 1
            hasMatched = False
            while s >= 0:
                if r<0:
                    return self.stack[:s+1] + (Parser.Nonterminal(clause.lhs,self.stack[s+1:]),)
                symbol = clause.rhs[r]
                matching = self.stack[s].matches(symbol)
                if not matching and hasMatched:
                    r -= 1
                    hasMatched = False
                    continue
                if not matching and symbol.modifier in ("just","some"):
                    return None
                if not matching and symbol.modifier in ("any","optional"):
                    r -= 1
                    hasMatched = False
                if matching and symbol.modifier in ("just","optional"):
                    s -= 1
                    r -= 1
                    hasMatched = False
                if matching and symbol.modifier in ("any","some"):
                    s -= 1
                    hasMatched = True
            if hasMatched and r==0:
                r -= 1
            if r<0:
                return self.stack[:s+1] + (Parser.Nonterminal(clause.lhs,self.stack[s+1:]),)
            return None

p = Parser(graph)
#p.parse("(())()((()())())", trace=open('trace.dot','wt'))
p.parse("()(()())()", trace=open('trace.dot','wt'))

