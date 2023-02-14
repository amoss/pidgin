from functools import total_ordering


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


def prefixesOf(s) :
    for i in range(1,len(s)+1):
        yield s[:i]

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


def partition(predicate, iterable):
    inside, outside = [], []
    for x in iterable:
        if predicate(x):
            inside.append(x)
        else:
            outside.append(x)
    return inside, outside


class Graph:
    class Node:
        def __init__(self, label):
            if isinstance(label,set):
                self.labels = label
            else:
                self.labels = set([label])

    class Edge:
        def __init__(self, source, target, label):
            self.source = source
            self.target = target
            self.label  = label
        def __hash__(self):
            return hash( (self.source, self.target, self.label) )
        def __eq__(self, other):
            return  self.source==other.source and self.target==other.target and self.label==other.label

    def __init__(self):
        self.nodes = set()
        self.nodeLabels = {}
        self.edges = set()
        self.start = None

    def findEdgeBySource(self, source):
        for e in self.edges:
            if e.source==source:
                yield e

    def findEdgeByTarget(self, target):
        for e in self.edges:
            if e.target==target:
                yield e

    def findEdgeByLabel(self, label):
        for e in self.edges:
            if e.label==label:
                yield e

    def force(self, label):
        '''Retrieve the node with the label if one exists otherwise create a node for the label.'''
        if isinstance(label,set):
            for l in label:
                if l in self.nodeLabels:
                    return self.nodeLabels[l]
            result = Graph.Node(label)
            self.nodes.add( result)
            for l in label:
                self.nodeLabels[l] = result
            return result
        else:
            if label in self.nodeLabels:
                return self.nodeLabels[label]
            result = Graph.Node(label)
            self.nodes.add( result )
            self.nodeLabels[label] = result
            return result

    def remove(self, node):
        #print(f"Removing {node}")
        self.edges = self.edges.difference(self.findEdgeBySource(node))
        self.edges = self.edges.difference(self.findEdgeByTarget(node))
        self.nodes = self.nodes.difference([node])
        self.nodeLabels = {k:v for k,v in self.nodeLabels.items() if v!=node}

    def connect(self, source, target, label):
        assert isinstance(source,Graph.Node) and source in self.nodes, str(source)
        assert isinstance(target,Graph.Node) and target in self.nodes, str(target)
        self.edges.add( Graph.Edge(source,target,label) )

    def fold(self, edge):
        #print(f"Folding {id(edge.source)} {id(edge.target)} {edge.label}")
        source = edge.source
        target = edge.target
        if source==target:
            self.edges.remove(edge)
            return

        outgoing  = set( [ (e.target, e.label) for e in self.findEdgeBySource(source) ] +
                         [ (e.target, e.label) for e in self.findEdgeBySource(target) ] )
        selfLoopsOut, outgoing = partition(lambda x:(x[0]==source or x[0]==target), outgoing)
        #print(f"Outgoing: {outgoing} {selfLoopsOut}")

        incoming  = set( [ (e.source, e.label) for e in self.findEdgeByTarget(source) ] +
                         [ (e.source, e.label) for e in self.findEdgeByTarget(target) ] )
        selfLoopsIn, incoming = partition(lambda x:(x[0]==source or x[0]==target), incoming)

        selfLoops = set( map(lambda x:x[1], selfLoopsOut)).union( map(lambda x:x[1], selfLoopsIn))
        selfLoops.difference(edge.label)

        self.remove(source)
        self.remove(target)
        srcLabel = source.labels if isinstance(source.labels, set) else set([source.labels])
        tarLabel = target.labels if isinstance(target.labels, set) else set([target.labels])
        merged = self.force(srcLabel.union(tarLabel))
        if self.start in (source,target):
            self.start = merged
        for (target,label) in outgoing:
            self.connect(merged, target, label)
        for (source,label) in incoming:
            self.connect(source, merged, label)
        for label in selfLoops:
            self.connect(merged, merged, label)

    def dot(self):
        print("digraph {")
        for n in self.nodes:
            label = "\\n".join([str(l) for l in n.labels])
            print(f'n{id(n)} [label="{label}"];')
        for e in self.edges:
            print(f'n{id(e.source)} -> n{id(e.target)} [label="{e.label}"];')
        print("}")

    def dump(self):
        for e in self.edges:
            print(e)

class Grammar:
    def __init__(self, start):
        self.rules    = dict()
        self.start    = start
        self.worklist = OrdSet()

    def add(self, rule):
        assert not rule.name in self.rules.keys()
        self.rules[rule.name] = rule

    def build(self):
        result = Graph()
        self.entry = Clause("<outside>", [Nonterminal(self.start)], terminating=True)
        self.worklist = OrdSet()
        self.worklist.add(self.entry.get(0))
        nodes = {}

        for config in self.worklist:
            configNode = result.force(config)
            if config.position < len(config.clause.rhs):
                sym = config.clause.rhs[config.position]
                if isinstance(sym, Terminal) or isinstance(sym, CalcTerminal):
                    succ = config.clause.get(config.position+1)
                    succNode = result.force(succ)
                    result.connect(configNode,succNode,sym) # "shift")
                    self.worklist.add(succ)
                    if sym.modifier in ("any","optional"):
                        result.connect(configNode, succNode, "predict")     # Match zero instancees
                    if sym.modifier in ("any","some"):
                        result.connect(configNode, configNode, sym) #  "shift")    # Back-edge for loop
                if isinstance(sym, Nonterminal):
                    rule = g.rules[sym.name]
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
        return result


class Terminal:
    def __init__(self, match, modifier="just", inverse=False):
        assert modifier in ["any", "just", "some", "optional"]
        if isinstance(match, str):
            self.string = match
            self.chars  = None
        else:
            self.chars  = set(match)
            self.string = None
        self.modifier = modifier
        self.inverse = inverse

    def __str__(self):
        if self.string is not None:
            return f"T({self.modifier},{self.string})"
        return f"T({self.modifier},{self.chars})"

    def order(self):
        if self.chars is not None:
            return (0, 0, self.chars)
        return (0, 1, self.string)

    def __eq__(self, other):
        return isinstance(other,Terminal) \
           and self.string==other.string \
           and self.chars==other.chars \
           and self.modifier==other.modifier \
           and self.inverse==other.inverse

    def __hash__(self):
        return hash((self.string,self.chars))

    def match(self, input):
        allowzero = self.modifier in ("any","optional")
        limit = len(input) if self.modifier in ("any","some") else 1
        if self.string is not None:
            assert self.modifier=="just", f"Can't match {self}"        # Lazy bastard achievement unlocked
            if input[:len(self.string)] == self.string:
                return self.string
            return None
        if self.chars is not None:
            i = 0
            while i<limit and ((input[i] not in self.chars) == self.inverse):
                i += 1
            if i==0:
                return "" if allowzero else None
            return input[:i]


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
        return isinstance(other,Nonterminal) and self.name==other.name and self.modifier==other.modifier

    def __hash__(self):
        return hash((self.name, self.modifier))


class CalcTerminal:
    def __init__(self, name, modifier="just"):
        assert modifier in ["any", "just", "some", "optional"]
        self.name = name
        self.modifier = modifier

    def order(self):
        return (2, 0, self.name)

    def __str__(self):
        return f"C({self.name})"

    def __eq__(self, other):
        return isinstance(other,CalcTerminal) and self.name==other.name and self.modifier==other.modifier




'''
list <- x+
g = Grammar("lst")
lst = Rule("lst")
lst.add([ Terminal("x","some") ])
g.add(lst)
'''

'''
list <- list x
      | x
g = Grammar("lst")
lst = Rule("lst")
lst.add([ Nonterminal("lst"), Terminal("x") ])
lst.add([ Terminal("x") ])
g.add(lst)
'''

'''
list <- list pair
      | pair
pair <- ( )
      | ( list )
'''
g = Grammar("lst")
lst = Rule("lst")
lst.add([ Nonterminal("lst"), Nonterminal("pair") ])
lst.add([ Nonterminal("pair") ])
pair = Rule("pair")
pair.add([ Terminal("("), Terminal(")") ])
pair.add([ Terminal("("), Nonterminal("pair","some"), Terminal(")") ])
g.add(lst)
g.add(pair)

'''
expr <- ( )
      | ( expr+ )

g = Grammar("expr")
expr = Rule("expr")
expr.add([ Terminal("("), Terminal(")") ])
expr.add([ Terminal("("), Nonterminal("expr","some"), Terminal(")") ])
g.add(expr)
'''

'''
expr <- ( expr* )
g = Grammar("expr")
expr = Rule("expr")
expr.add([ Terminal("("), Nonterminal("expr","any"), Terminal(")") ])
g.add(expr)
'''

graph = g.build()
#graph.dump()
while True:
    it = graph.findEdgeByLabel("predict")
    first = next(it,None)
    if first is None:
      break
    graph.fold(first)
graph.dot()

class Parser:

    class Terminal:
        def __init__(self, chars, tag=None):
            self.chars = chars
            self.tag = tag

        def matches(self, other):
            if not isinstance(other, Terminal):     # Grammar.Terminal
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

        def matches(self, other):
            if not isinstance(other, Nonterminal):  # Grammar.Nonterminal
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
            if r<0:
                return self.stack[:s+1] + (Parser.Nonterminal(clause.lhs,self.stack[s+1:]),)
            return None

    def __init__(self, graph):
        self.graph = graph

    def parse(self, input):
        self.states = set()
        self.states.add( Parser.State(self.graph.start, input, ()) )
        done = set()        ## Stratify sets by input length to avoid memory cost, i.e. iterate on all states of same input size in one batch
        counter = 0

        while len(self.states)>0:
            next = set()
            for s in self.states:
                print(f"State: {s.input} :: {' '.join([str(x) for x in s.stack])}")
                counter += 1
                if s.terminating() and len(s.input)==0 and len(s.stack)==1:
                    print("Success!!!!")
                    s.stack[0].dump()
                for edge in self.graph.findEdgeBySource(s.node):
                    if isinstance(edge.label, Terminal):
                        m = edge.label.match(s.input)
                        if m is not None:
                            print(f"  Shift {m} to {edge.target}")
                            next.add( Parser.State(edge.target, s.input[len(m):], s.stack + (Parser.Terminal(m),)) )
                    if isinstance(edge.label, Clause):
                        h = s.checkHandle(edge.label)
                        if h is not None:
                            print(f"  Reduce by {edge.label} onto {' '.join([str(x) for x in h])}")
                            next.add( Parser.State(edge.target, s.input, h) )

            done = done.union(self.states)
            next = next.difference(done)
            self.states = next
            print(f"Iteration with {len(next)} states")
        print(f"Processed {counter} states")


p = Parser(graph)
p.parse("(())()((()())())")
#p.parse("((()())())")

