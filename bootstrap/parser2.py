# Copyright (C) 2003 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import html
from .graph import Graph
from .grammar import Grammar

def prefixesOf(s) :
    for i in range(1,len(s)+1):
        yield s[:i]


class Parser:
    def __init__(self, graph, discard=None):
        self.graph = graph
        self.discard = discard

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
        done = {}        ## Stratify sets by input length to avoid memory cost, i.e. iterate on all states of same input size in one batch
        counter = 0
        traceEdges = []

        while len(self.states)>0:
            next = set()
            for s in self.states:
                counter += 1
                if s.terminating() and len(s.input)==0 and len(s.stack)==1:
                    if trace:
                        print(f"n{id(s)} [fillcolor=blue, style=filled];", file=trace)
                    yield s.stack[0]
                for edge in self.graph.findEdgeBySource(s.node):
                    if edge.label.isTerminal():
                        m = edge.label.match(s.input)
                        if m is not None:
                            if len(m)==0:
                                ns = Parser.State(edge.target, s.input, s.stack)
                            else:
                                remaining = s.input[len(m):]
                                if not edge.label.sticky and self.discard is not None:
                                    drop = self.discard.match(remaining)
                                    if drop is not None and len(drop)>0:
                                        remaining = remaining[len(drop):]
                                ns = Parser.State(edge.target, remaining, s.stack + (Parser.Terminal(m,edge.label),))
                            if not ns in done:
                                next.add(ns)
                                done[ns] = ns
                            else:
                                ns = done[ns]   # Canonical instance of state
                            if trace:
                                print(f'n{id(ns)} {Parser.stateProps(ns)}', file=trace)
                                traceEdges.append( (s,ns,"shift") )
                    else:
                        h = s.checkHandle(edge.label)
                        if h is not None:
                            ns = Parser.State(edge.target, s.input, h)
                            if not ns in done:
                                next.add(ns)
                                done[ns] = ns
                            else:
                                ns = done[ns]   # Canonical instance of state
                            if trace:
                                print(f'n{id(ns)} {Parser.stateProps(ns)}', file=trace)
                                traceEdges.append( (s,ns,"reduce") )

            self.states = next
        if trace:
            for src,tar,lab in traceEdges:
                print(f'n{id(src)} -> n{id(tar)} [label="{lab}"];', file=trace)
            print("}", file=trace)

    class Terminal:
        def __init__(self, chars, original, tag=None):
            self.chars    = chars
            self.tag      = tag
            self.original = original

        def __str__(self):
            return self.chars

        def __eq__(self, other):
            return isinstance(other,Parser.Terminal) and self.chars==other.chars and self.tag==other.tag \
                   and id(self.original)==id(other.original)

        def __hash__(self):
            return hash((self.chars,self.tag))

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
            return self.tag

        def __eq__(self, other):
            return isinstance(other,Parser.Nonterminal) and self.tag==other.tag and self.children==other.children

        def __hash__(self):
            return hash(self.tag)

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
            '''Handles are as complex as regex in this system, and so the choice of greediness is very important.
               It seems that greedy non-backtracking works on handles as long as we perform the match at the symbol
               level, and not the character-level. For terminals each Parser.Terminal on the stack contains a
               reference to the Grammar.Terminal it matched. For non-terminals we use the name.'''

            def strs(iterable):
                return " ".join([str(x) for x in iterable])
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
                    print(f"checkHandle fail1 on {s} {r} {clause.lhs} <- {strs(self.stack)} vs {strs(clause.rhs)}")
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
            print(f"checkHandle fail2 on {clause.lhs} <- {self.stack}")
            return None
