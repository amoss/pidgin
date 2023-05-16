# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import html
from .machine import SymbolTable, Automaton, Token, Handle, AState
from .util import OrdSet, strs

class Barrier:
    counter = 1
    '''Implementation for priority/greediness in the parse. A group of related PStates tied to passing a greedy
       symbol in a configuration (either NT any or NT some). The AState will contain the configuration before
       and after the greedy symbol (by the definition of the epsilon closure). The step after accepting the greedy
       symbol could be a transition or a reduction - but it will not be chosen until all of the other states in
       the barrier have run to completition. Every state in the barrier that arrives back at the gate state will
       update the delayed step to the state that has progressed furthest through the input.'''
    def __init__(self, continuation, parent=None):
        self.states = set()
        self.continuation = continuation
        self.parent = parent
        #print(f'Barrier {Barrier.counter}: {[[st.id for st in pri] for pri in continuation]}')
        self.id = Barrier.counter
        Barrier.counter += 1

    def __str__(self):
        return f'b{self.id}:{repr(self)}'

    def register(self, state):
        self.states.add(state)
        if self.parent is not None:
            self.parent.register(state)

    def cancel(self):
        for state in self.states:
            if state.barrier == self:
                state.barrier = None
        self.states = set()
        self.continuation = []

    def complete(self, state):
        #print(f'b{self.id} completes: {[p.id for p in self.states]} - {state.id}')
        self.states.remove(state)
        if len(self.states)==0:
            if self.parent is not None:
                self.parent.remove(state)
            return self, self.continuation
        return None, None

    def remove(self, state):
        self.states.remove(state)


# Note: there is no latching of states in this implementation. It is not needed for functional correctness,
#       but will be added later as it will reduce the number of barriers in the trace.
class PState:
    counter = 1
    '''A state of the parser (i.e. a stack and input position). In a conventional GLR parser this would
       just be the stack, but we are building a fused lexer/parser that operates on a stream of characters
       instead of terminals.'''
    def __init__(self, stack, position, processDiscard, keep=False, label="", barrier=None):
        self.stack          = stack
        self.position       = position
        self.id             = PState.counter
        self.processDiscard = processDiscard
        self.keep           = keep
        self.label          = label
        self.barrier        = barrier
        if barrier is not None:
            barrier.register(self)
        PState.counter += 1

    def __hash__(self):
        return hash((tuple(self.stack),self.position))

    def __eq__(self, other):
        return isinstance(other,PState) and self.stack==other.stack and self.position==other.position

    def enter(self, barrier):
        if barrier is not None:
            assert barrier.parent == self.barrier, f'p{self.id} {barrier} {barrier.parent} {self.barrier}'
            self.barrier = barrier
            barrier.register(self)

    def cancel(self):
        if self.barrier is not None:
            self.barrier.cancel()

    def complete(self):
        if self.barrier is not None:
            return self.barrier.complete(self)
        return None, None


    def successors(self, input):
        result = []
        astate = self.stack[-1]
        remaining = self.position
        if not self.keep:
            remaining += self.processDiscard(input[remaining:])
        #print(f'execute: {strs(self.stack)}')
        for priLevel in astate.edges:
            result.append([])
            #print(f'prilevel: {priLevel}')
            for edgeLabel,target in priLevel.items():
                #print(f'edge: {edgeLabel} target: {target}')
                if isinstance(edgeLabel, Automaton.Configuration) and isinstance(target,Handle):
                    newStack = target.check(self.stack)
                    #print(f'newStack={newStack}')
                    if newStack is not None:
                        #print(f'Handle match on old {strs(self.stack)}')
                        #print(f'                 => {strs(newStack)}')
                        if target.lhs is None:
                            result[-1].append(PState(newStack, self.position, self.processDiscard,
                                                     self.keep, "reduce", self.barrier))
                            continue
                        returnState = newStack[-2]
                        # When there is a merge in the automaton with identical edges coming into the same
                        # state from distinct prior states, handle checking must only follow the valid path
                        # in reverse.
                        if target.lhs in returnState.edges[0]:
                            newStack.append(returnState.edges[0][edgeLabel.lhs])
                            result[-1].append( PState(newStack, self.position, self.processDiscard, self.keep,
                                                      "reduce", self.barrier))
                elif isinstance(edgeLabel, SymbolTable.SpecialEQ) and edgeLabel.name=="glue":
                    result[-1].append( PState(self.stack[:-1] + [target], self.position,
                                              self.processDiscard, True, "shift", self.barrier))
                elif isinstance(edgeLabel, SymbolTable.SpecialEQ) and edgeLabel.name=="remover":
                    result[-1].append( PState(self.stack[:-1] + [target], remaining,
                                              self.processDiscard, False, "shift", self.barrier))
                else:
                    assert type(edgeLabel) in (SymbolTable.TermSetEQ,
                                               SymbolTable.TermStringEQ,
                                               SymbolTable.NonterminalEQ), type(edgeLabel)
                    matched = edgeLabel.matchInput(input[remaining:])
                    if matched is not None:
                        result[-1].append( PState(self.stack + [Token(edgeLabel,matched),target],
                                                  remaining+len(matched), self.processDiscard, self.keep,
                                                  "shift", self.barrier))
        return [ p for p in result if len(p)>0 ]

    def dotLabel(self, input, redundant):
        remaining = input[self.position:]
        astate = self.stack[-1]
        cell = ' bgcolor="#ffdddd"' if redundant else ''
        if not isinstance(astate,AState):
            return "<Terminated>"
        if len(remaining)>30:
            result =  f'< <table border="0"><tr><td{cell}>{html.escape(remaining[:30])}...</td></tr><hr/>'
        else:
            result =  f'< <table border="0"><tr><td{cell}>{html.escape(remaining)}</td></tr><hr/>'

        stackStrs = []
        for s in self.stack[-8:]:
            if isinstance(s, AState):
                stackStrs.append(f'<font color="blue">{s.label}</font>')
            else:
                stackStrs.append(html.escape(str(s)))
        result += f'<tr><td{cell}>' + " ".join([s for s in stackStrs]) + '</td></tr></table> >';
        return result



### The fold

#class Parser:
#    def __init__(self, grammar, discard=None, trace=None, ntTransformer={}, tTransformer={}):
#        self.grammar       = grammar
#        self.discard       = discard
#        self.tTransformer  = tTransformer
#        self.ntTransformer = ntTransformer
#        entry = Clause(None, [Grammar.Nonterminal(grammar.start)], terminating=True)
#        initial = AState(grammar, [entry.get(0)])
#        self.start = initial
#        worklist = OrdSet([initial])
#
#        for state in worklist:
#            nextSymbols = set( config.next() for config in state.configurations)
#            reducing = None in nextSymbols
#            nextSymbols.discard(None)
#            for symbol in nextSymbols:
#                possibleConfigs = [ c.succ() for c in state.configurations if c.next()==symbol ]
#                if symbol.modifier=="any":
#                    assert set(possibleConfigs) <= set(state.configurations), possibleConfigs  # By epsilon closure
#                    state.connect(symbol, state)    # No repeat on any as self-loop
#                elif symbol.modifier=="some":
#                    for p in possibleConfigs:
#                        next = AState(grammar, [c for c in state.configurations if c.next()==symbol], latch=p)
#                        next = worklist.add(next)
#                        state.connect(symbol, next)
#                else:
#                    next = AState(grammar, possibleConfigs)
#                    next = worklist.add(next)
#                    state.connect(symbol, next)
#            if reducing:
#                reducingConfigs = [ c for c in state.configurations if c.next() is None ]
#                for r in reducingConfigs:
#                    state.addReducer(r.clause)
#
#        self.states = worklist.set
#        assert isinstance(self.states, dict)
#
#    def dotAutomaton(self, output):
#        print("digraph {", file=output)
#        for s in self.states:
#            label = "\\n".join([str(c).replace('"','\\"') for c in s.configurations])
#            color = "color=grey" if s.latch is None else "color=black"
#            if len(s.byClause)>0:
#                print(f's{id(s)} [label="{label}",shape=rect,{color}];', file=output)
#            else:
#                print(f's{id(s)} [label="{label}",{color}];', file=output)
#            for t,next in s.byTerminal.items():
#                label = str(t).replace('"','\\"')
#                print(f's{id(s)} -> s{id(next)} [label="{label}"];', file=output)
#                if s.repeats[t]:
#                    print(f's{id(s)} -> s{id(s)} [label="{label}"];', file=output)
#            for name,next in s.byNonterminal.items():
#                print(f's{id(s)} -> s{id(next)} [label="NT({name})"];', file=output)
#                if s.repeats[name]:
#                    print(f's{id(s)} -> s{id(s)} [label="NT({name})"];', file=output)
#            for next in s.byGlue.values():
#                print(f's{id(s)} -> s{id(next)} [label="Glue"];', file=output)
#            for next in s.byRemover.values():
#                print(f's{id(s)} -> s{id(next)} [label="Remover"];', file=output)
#        print("}", file=output)
#
#    def prune(self, node):
#        if isinstance(node, Parser.Nonterminal):
#            if len(node.children)==1:
#                pruned = self.prune(node.children[0])
#            else:
#                result = [ self.prune(c) for c in node.children]
#                node.children = tuple(result)
#                pruned = node
#        else:
#            pruned = node
#
#        if isinstance(pruned, Parser.Nonterminal) and pruned.tag in self.ntTransformer:
#            return self.ntTransformer[pruned.tag](pruned)
#        if isinstance(pruned, Parser.Terminal) and pruned.tag in self.tTransformer:
#            return self.tTransformer[pruned.tag](pruned)
#        return pruned
#
#    def parse(self, input, trace=None):
#        barriers = set()
#        Barrier.counter = 1
#        if trace is not None:                    print("digraph {\nrankdir=LR;", file=trace)
#        pstates = [PState([self.start], 0, discard=self.discard)]
#        while len(pstates)>0:
#            next = []
#            for p in pstates:
#                if trace is not None:
#                    print(f"s{p.id} [shape=none,label={p.dotLabel(input)}];", file=trace)
#                    if p.barrier is not None:
#                        if p.barrier.id not in barriers:
#                            print(f'b{p.barrier.id} [fontcolor="blue",color="blue",label="Barrier {p.barrier.id}"];', file=trace)
#                            barriers.add(p.barrier.id)
#                        print(f's{p.id} -> b{p.barrier.id} [color="blue"];', file=trace)
#                if not isinstance(p.stack[-1],AState):
#                    remaining = p.position
#                    if not p.keep and self.discard is not None:
#                        drop = self.discard.match(input[p.position:])
#                        if drop is not None and len(drop)>0:
#                            remaining += len(drop)
#                    if remaining==len(input) and len(p.stack)==2:
#                        yield self.prune(p.stack[1])
#                        if trace is not None:    print(f"s{p.id} [shape=rect,label={p.dotLabel(input)}];", file=trace)
#                else:
#                    # Need to convert to single call otherwise we can't share barriers
#                    reduces = p.reductions()
#                    shifts  = p.shifts(input)
#                    next.extend(reduces)
#                    next.extend(shifts)
#                    if trace is not None:
#                        for r in reduces:
#                            print(f's{p.id} -> s{r.id} [label="reduce"];', file=trace)
#                        for s in shifts:
#                            print(f's{p.id} -> s{s.id} [label="shift"];', file=trace)
#                if p.barrier is not None:
#                    latch = p.barrier.cancel(p)
#                    if latch is not None:
#                        afterLatch = latch.liftAsLatch(input)
#                        if afterLatch is not None:
#                            next.append(afterLatch)
#                            if trace is not None: print(f'b{p.barrier.id} -> s{afterLatch.id} [color="blue"];', file=trace)
#            pstates = next
#        if trace is not None: print("}", file=trace)
#
#    class Terminal:
#        def __init__(self, chars, original):
#            self.chars    = chars
#            self.original = original
#            self.tag = original.tag
#
#        def __str__(self):
#            return self.chars
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
#            return str(self.tag)
#
#        def __eq__(self, other):
#            return isinstance(other,Parser.Nonterminal) and self.tag==other.tag and self.children==other.children
#
#        def __hash__(self):
#            return hash((self.tag,self.children))
#
#        def matches(self, other):
#            return isinstance(other,Grammar.Nonterminal) and self.tag == other.name
#
#        def dump(self, depth=0):
#            print(f"{'  '*depth}{self.tag}")
#            for c in self.children:
#                c.dump(depth+1)
