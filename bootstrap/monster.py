# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from functools import total_ordering
import html
import itertools
import sys
from .grammar import Rule, Clause, Grammar
from .machine import Handle, AState, Token
from .util import strs, OrdSet, MultiDict



class Barrier:
    counter = 1
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


class SymbolTable:
    '''The collection of canonical equivalence-classes for symbols.'''
    def __init__(self):
        self.classes = [SymbolTable.SpecialEQ("glue"), SymbolTable.SpecialEQ("remover")]
        self.lookup  = { ('glue',):0, ('remover',):1 }

    def makeConfig(self, clause, position=0):
        assert isinstance(clause, Clause)
        if clause.lhs is None:
            newLhs = None
        else:
            newLhs = self.get(('nt', clause.lhs), lambda: SymbolTable.NonterminalEQ(clause.lhs))
        return Automaton.Configuration(newLhs, self.canonSentence(clause.rhs, clause=clause), position=position)

    def canonSentence(self, rhs, clause=None):
        result = []
        for i,s in enumerate(rhs):
            if isinstance(s,Grammar.Glue):
                key = ('glue',)
            if isinstance(s,Grammar.Remover):
                key = ('remover',)
            if isinstance(s,Grammar.TermSet):
                key = (clause,i)
                cons = lambda: SymbolTable.TermSetEQ(s.chars,inverse=s.inverse)
            if isinstance(s,Grammar.TermString):
                key = ('t', s.string)
                cons = lambda: SymbolTable.TermStringEQ(s.string)
            if isinstance(s,Grammar.Nonterminal):
                key = ('nt', s.name)
                cons = lambda: SymbolTable.NonterminalEQ(s.name)
            sClass = self.get(key,cons)
            result.append(Symbol(sClass, s.modifier, s.strength))
        return result

    class TermSetEQ:
        def __init__(self, chars, inverse=False):
            self.chars   = chars
            self.inverse = inverse
            self.isTerminal    = True
            self.isNonterminal = False
        def __str__(self):
            return f'[{self.index}]'
        def html(self, modifier=''):
            return f'<FONT face="monospace">[{self.index}]</FONT>{modifier}'
        def isTerminal(self):
            return True
        def isNonterminal(self):
            return False
        def matchInput(self, input):
            if len(input)==0:                                   return None
            if (input[0] not in self.chars) == self.inverse:    return input[:1]
            return None

    class TermStringEQ:
        def __init__(self, literal):
            self.literal = literal
            self.isTerminal    = True
            self.isNonterminal = False
        def __str__(self):
            return self.literal
        def html(self, modifier=''):
            return f'<FONT face="monospace" color="grey">{html.escape(self.literal)} </FONT>{modifier}'
        def matchInput(self, input):
            if len(input)==0:                                   return None
            if input[:len(self.literal)]==self.literal:         return self.literal
            return None

    class NonterminalEQ:
        def __init__(self, name):
            self.name = name
            self.isTerminal    = False
            self.isNonterminal = True
        def __str__(self):
            return f'N({self.name})'
        def html(self, modifier=''):
            return self.name + modifier
        def matchInput(self, input):
            return None

    class SpecialEQ:
        def __init__(self, name):
            self.name = name
            self.isTerminal    = False
            self.isNonterminal = False
        def __str__(self):
            return self.name
        def html(self, modifier=''):
            return f'<FONT color="grey"><B>{self.name}</B></FONT>'


    def get(self, key, cons):
        if key in self.lookup:
            return self.classes[self.lookup[key]]
        self.lookup[key] = len(self.classes)
        newClass = cons()
        newClass.index = len(self.classes)
        self.classes.append(newClass)
        return newClass


class Symbol:
    def __init__(self, eqClass, modifier="just", strength="greedy"):
        self.eqClass  = eqClass
        self.modifier = modifier
        self.strength = strength

    def __str__(self):
        if self.modifier=="just":     return str(self.eqClass)
        if self.modifier=="any":      return str(self.eqClass) + '*'
        if self.modifier=="some":     return str(self.eqClass) + '+'
        if self.modifier=="optional": return str(self.eqClass) + '?'

    def isTerminal(self):
        return self.eqClass.isTerminal

    def isNonterminal(self):
        return self.eqClass.isNonterminal




class Automaton:
    def canonicalizeGrammar(self, grammar):
        '''Rebuild grammar with initial configurations replacing each clause, where the configurations contain
           Symbols linked to canonical equivalence classes.'''
        self.canonGrammar = {}
        self.symbolTable = SymbolTable()
        for rule in grammar.rules.values():
            s = set()
            for clause in rule.clauses:
                s.add(self.symbolTable.makeConfig(clause))
            self.canonGrammar[rule.name] = s


    def __init__(self, grammar):
        self.canonicalizeGrammar(grammar)
        if grammar.discard is None:
            self.processDiscard = lambda input: 0
        else:
            discardSymbol = self.symbolTable.canonSentence([grammar.discard])[0].eqClass
            def pDiscard(input):
                m = 0
                while discardSymbol.matchInput(input[m:]) is not None:
                    m += 1
                return m
            self.processDiscard = lambda input: pDiscard(input)

        entry = Automaton.Configuration(None, self.symbolTable.canonSentence([Grammar.Nonterminal(grammar.start)])) # terminating?
        initial = AState(self.canonGrammar, [entry], label='s0')
        self.start = initial
        worklist = OrdSet([initial])
        counter = 1

        for state in worklist:
            active = [c for c in state.configurations if c.next() is not None ]
            for pri, priLevel in enumerate(state.edges):
                for eqClass in priLevel.keys():
                    if isinstance(eqClass, Automaton.Configuration):
                        state.addEdge(pri, eqClass, Handle(eqClass))
                        if eqClass.hasReduceBarrier():
                            below = eqClass.floor()
                            state.addEdge(pri+1, below, Handle(below))
                    else:
                        matchingConfigs = [ c for c in active if c.next().eqClass==eqClass ]
                        possibleConfigs = [ c.succ() for c in matchingConfigs ] + \
                                          [ c        for c in matchingConfigs if c.next().modifier in ('any','some') ]
                        assert len(possibleConfigs)>0, str(eqClass)
                        next = AState(self.canonGrammar, possibleConfigs, label=f's{counter}')
                        counter += 1
                        next = worklist.add(next)
                        priLevel[eqClass] = next


        self.states = worklist.set
        assert isinstance(self.states, dict)

    def dot(self, output):
        def makeNextId(state, next, symbol, output):
            if next is None:
                nextId = f's{id(state)}_{id(symbol)}'
                print(f'{nextId} [color=red,label="missing"];', file=output)
            else:
                nextId = f's{id(next)}'
            return nextId
        def priColor(pri):
            if pri==0:  return 'black'
            if pri==1:  return 'grey30'
            if pri==2:  return 'grey60'
            return 'grey90'

        print("digraph {", file=output)
        for s in self.states:
            label = "<BR/>".join([c.html() for c in s.configurations])
            print(f's{id(s)} [shape=none,label=<<font color="blue">{s.label}</font>{label} >];', file=output)

            for pri,priLevel in enumerate(s.edges):
                color = priColor(pri)
                for edgeLabel,next in priLevel.items():
                    if isinstance(edgeLabel, Automaton.Configuration):
                        nextId = f's{id(s)}_{id(edgeLabel)}'
                        print(f'{nextId} [shape=rect,label=<reduce {edgeLabel.html()}>];', file=output)
                        print(f's{id(s)} -> {nextId} [color={color},label=<{edgeLabel.html()}>];', file=output)
                    else:
                        assert type(edgeLabel) in (SymbolTable.TermSetEQ,
                                                   SymbolTable.TermStringEQ,
                                                   SymbolTable.NonterminalEQ,
                                                   SymbolTable.SpecialEQ), type(edgeLabel)
                        nextId = makeNextId(s, next, edgeLabel, output)
                        if edgeLabel.isTerminal:
                            print(f's{id(s)} -> {nextId} [color={color},label=<shift {edgeLabel.html()}>];', file=output)
                        elif edgeLabel.isNonterminal:
                            print(f's{id(s)} -> {nextId} [color=grey,label=<<FONT color="grey">accept {edgeLabel.name}</FONT>>];', file=output)
                        else:
                            print(f's{id(s)} -> {nextId} [label=<{edgeLabel.html()}>];', file=output)
        print("}", file=output)

    def execute(self, input, tracing=False):
        self.trace = Automaton.Trace(input, tracing)
        pstates = [PState([self.start], 0, self.processDiscard)]
        while len(pstates)>0:
            next = []
            for p in pstates:
                #print(f'Execute p{p.id} {strs(p.stack)}')
                self.trace.barrier(p)
                if not isinstance(p.stack[-1],AState):
                    remaining = p.position + self.processDiscard(input[p.position:])
                    if remaining==len(input) and len(p.stack)==2:
                        yield p.stack[1]
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

    class Configuration:
        def __init__(self, lhs, rhs, position=0):
            self.lhs      = lhs
            self.rhs      = tuple(rhs)
            self.position = position

        def __str__(self):
            return f'{self.lhs} <- ' + " ".join(['^'+str(s) if self.position==i else str(s)
                                                            for i,s in enumerate(self.rhs)]) \
                                     + ('^' if self.position==len(self.rhs) else '')
        def html(self):
            result = f"{self.lhs} &larr; "
            for i,s in enumerate(self.rhs):
                if i==self.position:
                    result += '<SUB><FONT color="blue">&uarr;</FONT></SUB>'
                modChars = { 'just':'', 'any':'*', 'some':'+', 'optional':'?' }
                result += s.eqClass.html(modifier=modChars[s.modifier])
            if self.position==len(self.rhs):
                result += '<SUB><FONT color="blue">&uarr;</FONT></SUB>'
            return result

        def sig(self):
            return (self.lhs, self.rhs, self.position)

        def __eq__(self, other):
            return isinstance(other, Automaton.Configuration) and self.sig()==other.sig()

        def __hash__(self):
            return hash(self.sig())

        def next(self):
            if self.position==len(self.rhs):  return None
            return self.rhs[self.position]

        def succ(self):
            assert self.position < len(self.rhs)
            return Automaton.Configuration(self.lhs, self.rhs, position=self.position+1)

        def isReducing(self):
            return self.position == len(self.rhs)

        def hasReduceBarrier(self):
            return self.floor()!=self

        def floor(self):
            isBarrier = lambda s: s.isNonterminal() and s.modifier in ('any','some') and s.strength!='all'
            return Automaton.Configuration(self.lhs, [symbol for symbol in self.rhs if not isBarrier(symbol)],
                                           position=self.position)

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
            self.calculateRedundancy()
            found, completed = set(), set()
            nodes = set(self.forwards.map.keys()) | set(self.backwards.map.keys())
            print('digraph {', file=target)
            for n in nodes:
                if isinstance(n, PState):
                    print(f'p{n.id} [shape=none, ' +
                          f'label={n.dotLabel(self.input,self.redundant[n])}];', file=target)
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


if __name__ == '__main__':
    def T(val, m=None, s=None):
        if m is None:
            if isinstance(val,str):
                return Grammar.TermString(val)
            return Grammar.TermSet(val)
        if isinstance(val,str):
            return Grammar.TermString(val, modifier=m)
        return Grammar.TermSet(val, modifier=m, strength=s)


    def N(name, modifier='just', strength='greedy'):
        return Grammar.Nonterminal(name, modifier=modifier, strength=strength)
    g = Grammar('R')
    g.addRule('R', [T('x','any'), T('y','any'), T('z','any')])
    a = Automaton(g)
    a.dot( open('eclr.dot','wt') )
    for result in a.execute('xxxzz',True):
        print(result)
    a.trace.output(open('x.dot','wt'))
    print(a.trace.measure())
