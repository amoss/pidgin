# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import html
from .machine import SymbolTable, Automaton, Handle, AState, Symbol
from .util import MultiDict, OrdSet, strs, dump

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
                    newStack, handle = target.check(self.stack)
                    #print(f'newStack={newStack}')
                    if newStack is not None:
                        #print(f'Handle match on old {strs(self.stack)}')
                        #print(f'                 => {strs(newStack)}')
                        if target.lhs is None:
                            # This is the synthesized rule that acted as entry point, unpack result
                            assert len(handle)==1
                            newStack.append( handle[0] )
                            result[-1].append(PState(newStack, self.position, self.processDiscard,
                                                     self.keep, "reduce", self.barrier))
                            continue
                        newStack.append( Token(target.lhs,handle,None) )
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
                        result[-1].append( PState(self.stack + [Token(edgeLabel,(),matched),target],
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


class Token:
    def __init__(self, symbol, children, span):
        self.symbol   = symbol
        if hasattr(symbol,'tag'):
            self.tag = symbol.tag
        elif hasattr(symbol,'name'):
            self.tag = symbol.name
        else:
            self.tag = None
        assert type(symbol) in (SymbolTable.TermSetEQ, SymbolTable.TermStringEQ, SymbolTable.NonterminalEQ),\
               f'{symbol} is {repr(symbol)}'
        self.children = children
        self.span     = span
        for c in children:
            assert isinstance(c, Token), c


    def __str__(self):
        if self.symbol is not None and self.symbol.isTerminal:
            return f'T({self.span})'
        return f'N({self.symbol.name})'


    def dump(self, depth=0):
        print(f"{'  '*depth}{self}")
        for c in self.children:
            if isinstance(c, Token):
                c.dump(depth+1)
            else:
                print(f"{'  '*(depth+1)}{c}")


class Parser:
    def __init__(self, machine, ntTransformer={}, tTransformer={}):
        self.machine = machine
        self.tTransformer  = tTransformer
        self.ntTransformer  = ntTransformer

    def execute(self, input, tracing=False):
        self.trace = Trace(input, tracing)
        pstates = [PState([self.machine.start], 0, self.machine.processDiscard)]
        while len(pstates)>0:
            next = []
            for p in pstates:
                #print(f'Execute p{p.id} {strs(p.stack)}')
                self.trace.barrier(p)
                if not isinstance(p.stack[-1],AState):
                    remaining = p.position + self.machine.processDiscard(input[p.position:])
                    if remaining==len(input) and len(p.stack)==2:
                        yield self.prune(p.stack[1])
                        p.cancel()
                        self.trace.result(p)
                        continue
                    else:
                        self.trace.blocks(p)
                        # Fall-through to completion
                else:
                    #try:
                    succ = p.successors(input)
                    #print(f'succ {[[st.id for st in pri] for pri in succ]}')
                    if len(succ)==0:
                        self.trace.blocks(p)
                    else:
                        barrier = None
                        if len(succ)>1:
                            barrier = Barrier(succ[1:], parent=p.barrier)
                            #print(f'p{p.id} creates b{barrier.id}: {barrier}')

                        for state in succ[0]:
                            if state.label=="shift":
                                self.trace.shift(p,state)
                            else:
                                self.trace.reduce(p,state)
                            next.append(state)
                            state.enter(barrier)
                    #except AssertionError as e:
                    #    self.trace.blocks(p)
                    #    print(f'ERROR {e}')
                closedBarrier, continuation = p.complete()
                if continuation is not None:
                    barrier = None
                    if len(continuation)>1:
                        barrier = Barrier(continuation[1:], closedBarrier.parent)

                    for state in continuation[0]:
                        if state.label=="shift":
                            self.trace.shift(closedBarrier, state)
                        else:
                            self.trace.reduce(closedBarrier, state)
                        next.append(state)
                        state.enter(barrier)

            #print(f'next {[st.id for st in next]}')
            pstates = next

    def prune(self, node):
        if not isinstance(node,Token):      return node
        if node.symbol.isNonterminal:
            if len(node.children)==1:
                pruned = self.prune(node.children[0])
            else:
                result = [ self.prune(c) for c in node.children]
                node.children = tuple(result)
                pruned = node
        else:
            pruned = node
        if not isinstance(pruned,Token):    return pruned
        try:
            if pruned.symbol.isNonterminal and pruned.symbol.name in self.ntTransformer:
                return self.ntTransformer[pruned.symbol.name](pruned)
            if pruned.symbol.isTerminal and pruned.tag in self.tTransformer:
                return self.tTransformer[pruned.tag](pruned)
        except:
            print(f'Failed to apply transformer to:')
            dump(pruned)
            raise

        return pruned



class Trace:
    def __init__(self, input, recording):
        self.recording = recording
        self.input     = input
        self.forwards  = MultiDict()
        self.backwards = MultiDict()
        self.redundant = None

    def shift(self, source, destination):
        if not self.recording: return
        assert source is not None
        assert destination is not None
        self.forwards.store(source,  (destination, 'shift'))
        self.backwards.store(destination, (source, 'shift'))

    def reduce(self, source, destination):
        if not self.recording: return
        assert source is not None
        assert destination is not None
        self.forwards.store(source,  (destination, 'reduce'))
        self.backwards.store(destination, (source, 'reduce'))

    def result(self, state):
        if not self.recording: return
        assert state is not None
        self.forwards.store(state, (True, 'emit'))
        self.backwards.store(True, (state,'emit'))

    def blocks(self, state):
        if not self.recording: return
        assert state is not None
        self.forwards.store(state, (False, 'blocks'))
        self.backwards.store(False, (state,'blocks'))

    def barrier(self, pstate):
        if not self.recording: return
        if pstate.barrier is None: return
        self.forwards.store(pstate,  (pstate.barrier, 'barrier'))
        self.backwards.store(pstate.barrier, (pstate, 'barrier'))


    def output(self, target):
        from .parser import PState, Barrier      #### TEMP TEMP TEMP
        self.calculateRedundancy()
        found, completed = set(), set()
        nodes = set(self.forwards.map.keys()) | set(self.backwards.map.keys())
        print('digraph {', file=target)
        for n in nodes:
            if isinstance(n, PState):
                print(f'p{n.id} [shape=none, ' +
                      f'label={n.dotLabel(self.input,self.redundant.get(n,True))}];', file=target)
            elif isinstance(n, Barrier):
                print(f'b{n.id} [shape=none, fontcolor=orange, label="Barrier {n.id}"];', file=target)
                if n.parent is not None:
                    print(f'b{n.parent.id} -> b{n.id} [label="nested", fontcolor=orange, color=orange]',
                          file=target)
            elif n not in (True,False):
                print(f'Unrecognised node in trace: {repr(n)}')

        for k,v in self.forwards.map.items():
            if isinstance(k, PState):
                for nextState, label in v:
                    fontcolor = 'black'
                    if isinstance(nextState,PState):
                        print(f'p{k.id} -> p{nextState.id} [label="{label}"];', file=target)
                    elif isinstance(nextState,Barrier):
                        print(f'p{k.id} -> b{nextState.id} [label="inside",color=orange,fontcolor=orange];', file=target)
            elif isinstance(k, Barrier):
                for nextState, label in v:
                    print(f'b{k.id} -> p{nextState.id} [label="continues",color=orange,fontcolor=orange];', file=target)
        print('}', file=target)

    def calculateRedundancy(self):
        if self.redundant is not None: return
        self.redundant = {}
        for k in self.forwards.map.keys():
            self.redundant[k] = True
        # The backwards map over the trace is acyclic and performance is not a concern
        def markAncestors(state):
            if not state in self.backwards.map:
                pass #print(f'Orphan {state}')
            else:
                for next,_ in self.backwards.map[state]:
                    self.redundant[next] = False
                    markAncestors(next)
        if True in self.backwards.map:
            for s,_ in self.backwards.map[True]:
                markAncestors(s)

    def measure(self):
        self.calculateRedundancy()
        redundant = self.redundant.values()
        return len([v for v in redundant if v]) / len(redundant)

    def solutions(self):
        if True in self.backwards.map:
            for s,_ in self.backwards.map[True]:
                yield s

