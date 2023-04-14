# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from functools import total_ordering
import html
import itertools
import sys

def strs(iterable):
    return " ".join([str(x) for x in iterable])


class OrdSet:
    '''This class differs from collections.OrderedDict because we can mutate it while iterating over it. The
       add method returns the value to allow canonical values.'''
    def __init__(self, initial=[]):
        self.set = {}
        self.ord = []
        for x in initial:
            self.add(x)

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

class MultiDict:
    '''This class stores a representation of graph edges as a two-level structure of keys -> value(-sets).'''
    def __init__(self):
        self.map = {}

    def store(self, k, v):
        if not k in self.map.keys():
            self.map[k] = set()
        self.map[k].add(v)




class Rule:
    def __init__(self, name, grammar):
        self.name = name
        self.grammar = grammar
        self.clauses = set()

    def add(self, initialBody):
        body = [ self.grammar.canonical(symbol) if symbol.isTerminal() else symbol
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

    def html(self):
        result = ""
        for s in self.rhs:
            modChars = { 'just':'', 'any':'*', 'some':'+', 'optional':'?' }
            modifier = modChars[s.modifier]
            if isinstance(s,Grammar.Nonterminal):
                result += s.name + f"{modifier} "
            elif isinstance(s,Grammar.TermString):
                result += f'<FONT face="monospace" color="grey">{html.escape(s.string)} </FONT>{modifier}'
            elif isinstance(s,Grammar.TermSet):
                result += f'<FONT face="monospace">[]</FONT>{modifier}'
            else:
                result += str(type(s)) + modifier
        return result

    def isTerminal(self):
        return False

    def get(self, position):
        if self.configs[position] is None:
            self.configs[position] = Configuration(self, position)
        return self.configs[position]

    def hasReduceBarrier(self):
        for symbol in self.rhs:
            if isinstance(symbol,Grammar.Nonterminal) and \
                    symbol.modifier in ('any','some') and \
                    symbol.strength in ('greedy','frugal'):
                return True
        return False

    def floor(self):
        return Clause(self.lhs, [symbol for symbol in self.rhs
                                        if not (isinstance(symbol,Grammar.Nonterminal) and \
                                           symbol.modifier in ('any','some') and \
                                           symbol.strength in ('greedy','frugal'))])

class Configuration:
    def __init__(self, clause, position):
        self.clause = clause
        assert -1 <= position and position <= len(self.clause.rhs)
        self.position = position
        self.terminating = clause.terminating and self.isReducing()

    def __str__(self):
        result = f"{self.clause.lhs} <- "
        for i,s in enumerate(self.clause.rhs):
            if i==self.position:
                result += "*"
            result += str(s)
        if self.position==len(self.clause.rhs):
            result += "*"
        return result

    def html(self):
        result = f"{self.clause.lhs} &larr; "
        for i,s in enumerate(self.clause.rhs):
            if i==self.position:
                result += '<SUB><FONT color="blue">&uarr;</FONT></SUB>'
            modChars = { 'just':'', 'any':'*', 'some':'+', 'optional':'?' }
            modifier = modChars[s.modifier]
            if isinstance(s,Grammar.Nonterminal):
                result += s.name + f"{modifier} "
            elif isinstance(s,Grammar.TermString):
                result += f'<FONT face="monospace" color="grey">{html.escape(s.string)} </FONT>{modifier}'
            elif isinstance(s,Grammar.TermSet):
                result += f'<FONT face="monospace">[]</FONT>{modifier}'
            else:
                result += str(type(s)) + modifier
        if self.position==len(self.clause.rhs):
            result += '<SUB><FONT color="blue">&uarr;</FONT></SUB>'
        return result

    def __eq__(self, other):
        if not isinstance(other,Configuration):
            return False
        return self.clause.lhs==other.clause.lhs and self.position==other.position and\
               self.clause.rhs==other.clause.rhs

    def __hash__(self):
        return hash((self.clause.lhs, str(self.clause.rhs), self.position))

    def isReducing(self):
        return self.position == len(self.clause.rhs)

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
        assert terminal.isTerminal(), terminal
        if not terminal in self.canonicalTerminals:
            self.canonicalTerminals[terminal] = terminal
        return self.canonicalTerminals[terminal]

    def addRule(self, name, *body):
        assert not name in self.rules.keys()
        rule = Rule(name, self)
        for b in body:
            rule.add(b)
        self.rules[name] = rule
        return rule

    def setDiscard(self, terminal):
        self.discard = terminal

    def dump(self):
        for rule in self.rules.values():
            print(f"{rule.name}:")
            for clause in rule.clauses:
                print(f"  {strs(clause.rhs)}")

    class TermString:
        def __init__(self, match, modifier="just", tag=''):
            '''A terminal symbol that matches a string literal *match*. If the *modifier* is repeating then
               the match is always greedy. If non-greedy matching is required then it can be simulated by
               wrapping in a non-terminal (with glue if appropriate).'''
            self.string = match
            self.tag = tag
            assert modifier in ("any","just","some","optional"), modifier
            self.modifier = modifier

        def __str__(self):
            tag = f",{self.tag}" if self.tag!="" else ""
            return f"T({repr(self.string)},{self.modifier}{tag})"

        def html(self):
            return html.escape(self.string)

        def sig(self):
            return (self.string, self.tag, self.modifier)

        def __eq__(self,other):
            return isinstance(other,Grammar.TermString) and self.sig()==other.sig()

        def eqOne(self,other):
            '''Ignoring the modifier, would a single instance of this terminal match?'''
            return isinstance(other,Grammar.TermString) and self.string==other.string

        def __hash__(self):
            return hash(self.sig())

        def isTerminal(self):
            return True

        def match(self, input):
            limit = len(input) if self.modifier in ("any","some") else 1
            i = 0
            n = len(self.string)
            original = input[:]
            #print(f"Matching {i} {n} {self.string} {input}")
            while i<limit and input[:n]==self.string:
                i += 1
                input = input[n:]
                #print(f"Matching {i} {n} {self.string} {input}")
            if i>0:
                return original[:i*n]

        def exactlyOne(self):
            return Grammar.TermString(self.string, modifier="just", tag=self.tag)

        # Does this still get used or is it dead?
        #def order(self):
        #    return (0, 1, self.string)

    class TermSet:
        def __init__(self, charset, modifier="just", inverse=False, tag=''):
            assert modifier in ("any","just","some","optional"), modifier
            self.modifier = modifier
            self.chars = frozenset(charset)
            self.inverse  = inverse
            self.tag      = tag

        def __str__(self):
            if len(self.chars)<=5:
                charset = "".join([c for c in self.chars])
            else:
                charset = "".join([c for c in list(self.chars)[:5]]) + f' +{len(self.chars)-5}'
            if self.inverse:
                result = 'T(^{' + charset + '}'
            else:
                result = 'T({' + charset + '}'
            tag = f",{self.tag}" if self.tag!="" else ""
            return f'{result},{self.modifier}{tag})'

        def html(self):
            return '[]'

        def sig(self):
            return (self.chars, self.modifier, self.inverse, self.tag)

        def __eq__(self,other):
            return isinstance(other,Grammar.TermSet) and self.sig()==other.sig()

        def eqOne(self,other):
            '''Ignoring the modifier, would a single instance of this terminal match?'''
            return isinstance(other,Grammar.TermSet) and self.chars==other.chars and self.inverse==other.inverse

        def __hash__(self):
            return hash(self.sig())

        def isTerminal(self):
            return True

        def exactlyOne(self):
            return Grammar.TermSet(self.chars, modifier="just", inverse=self.inverse, tag=self.tag)

        # Does this still get used or is it dead?
        #def order(self):
        #    return (0,0,self.chars)

        def match(self, input):
            limit = len(input) if self.modifier in ("any","some") else 1
            i = 0
            while i<limit and i<len(input) and ((input[i] not in self.chars) == self.inverse):
                i += 1
            if i>0:
                return input[:i]


    class Nonterminal:
        def __init__(self, name, strength="greedy", modifier="just"):
            assert modifier in ("any", "just", "some", "optional"), modifier
            assert strength in ("all", "frugal", "greedy"), strength
            self.name     = name
            self.modifier = modifier
            self.strength = strength

        def __str__(self):
            return f"N({self.strength},{self.modifier},{self.name})"

        # Does this still get used or is it dead?
        #def order(self):
        #    return (1, 0, self.name)

        def sig(self):
            return (self.name, self.modifier)

        def __eq__(self, other):
            return isinstance(other,Grammar.Nonterminal) and self.sig()==other.sig()

        def __hash__(self):
            return hash(self.sig())

        def eqOne(self, other):
            return isinstance(other,Grammar.Nonterminal) and self.name==other.name

        def isTerminal(self):
            return False

        def exactlyOne(self):
            return Grammar.Nonterminal(self.name, strength=self.strength, modifier="just")

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
            return hash((1,self.within,self.position))

        def isTerminal(self):
            return False

    class Remover:
        def __init__(self):
            self.within = None
            self.position = None
            self.modifier = "just"

        def __str__(self):
            return "Remover"

        def __eq__(self, other):
            return isinstance(other,Grammar.Remover) and self.within==other.within and self.position==other.position

        def __hash__(self):
            return hash((2,self.within,self.position))

        def isTerminal(self):
            return False




def barrierSources(trace, terminal):
    '''Each entry in the *trace* is a map from symbol to sources that it was derived from during epsilon-closure.
       This representation is necessary as the relation may form a DAG instead of a tree. From the given *terminal*
       walk back through the DAG and check for greedy repeating symbols.'''
    result = set()
    worklist = OrdSet()
    for src in trace[terminal]:
        worklist.add(src)
    for item in worklist:
        if isinstance(item,str) and item in trace:
            for src in trace[item]:
                worklist.add(src)
        elif isinstance(item,Grammar.Nonterminal) and item.modifier in ('any','some') and item.strength in ('greedy','frugal'):
            result.add(item)
    return result


class Handle:
    def __init__(self, clause):
        '''Build a restricted NFA for recognising the clause - no loops larger than self-loops, no choices.
           The NFA is a straight-line with self-loops on repeating nodes and jumps over skipable nodes.
           Translate the NFA to a DFA that we store / use for recognition.'''
        nfaStates  = list(reversed(clause.rhs))
        nfaSkips   = [ s.modifier in ('optional','any') for s in nfaStates ] + [False]
        nfaRepeats = [ s.modifier in ('some','any') for s in nfaStates ]     + [False]
        nfaEdges   = [ MultiDict() for i in range(len(nfaStates)) ]          + [MultiDict()]

        for i,s in enumerate(nfaStates):
            if nfaRepeats[i]:
                nfaEdges[i].store(s.exactlyOne(), i)
            for tar in range(i+1,len(nfaStates)+2):
                nfaEdges[i].store(s.exactlyOne(), tar)
                if not nfaSkips[tar]:
                    break

        initial = []
        for i in range(len(nfaStates)+1):
            initial.append(i)
            if not nfaSkips[i]:
                break
        self.initial = frozenset(initial)
        self.exit = len(nfaStates)
        self.lhs = clause.lhs

        def successor(dfaState, symbol):
            result = set()
            for nfaIdx in dfaState:
                if symbol in nfaEdges[nfaIdx].map:
                    result.update(nfaEdges[nfaIdx].map[symbol])
            return frozenset(result)

        def ogEdges(dfaState):
            result = set()
            for nfaIdx in dfaState:
                for symbol in nfaEdges[nfaIdx].map.keys():
                    result.add(symbol)
            return result

        self.dfa = MultiDict()
        worklist = OrdSet()
        worklist.add(self.initial)
        for state in worklist:
            if state in self.dfa.map:
                continue
            for symbol in ogEdges(state):
                succ = successor(state,symbol)
                self.dfa.store(state, (symbol,succ))
                worklist.add(succ)

    def check(self, stack):
        '''Check the stack against the DFA. If we find a match then return the remaining stack after the
           handle has been removed.'''
        assert isinstance(stack[-1], AState), stack[-1]
        assert (len(stack)%2) == 1
        pos = len(stack)-2
        dfaState = self.initial
        while pos>0:
            next = None
            if dfaState in self.dfa.map:   # If dfaState = { nfaExit } then it won't be in the edge map
                for symbol, succ in self.dfa.map[dfaState]:
                    #print(f'pos={stack[pos]} pos-1={stack[pos-1].validLhs}')
                    if stack[pos].matches(symbol) and self.lhs in stack[pos-1].validLhs:
                        next = succ
                        pos -= 2
                        break
            if next is None:
                if self.exit in dfaState:
                    onlySymbols = ( s for s in stack[pos+2:] if not isinstance(s,AState) )
                    return stack[:pos+2] + [Automaton.Nonterminal(self.lhs,onlySymbols)]
                return None
            dfaState = next
        if self.exit in dfaState:
            onlySymbols = ( s for s in stack[pos+2:] if not isinstance(s,AState) )
            return stack[:pos+2] + [Automaton.Nonterminal(self.lhs,onlySymbols)]
        return None


class AState:
    counter = 1
    '''A state in the LR(0) automaton'''
    def __init__(self, grammar, configs, label=None):
        assert len(configs)>0
        self.grammar = grammar
        self.byPriTerminal   = {}
        self.shiftBarriers   = {}
        self.byTerminal      = {}
        self.byNonterminal   = {}
        self.byClause        = {}
        self.byPriClause     = {}
        self.reduceBarriers  = {}
        if label is None:
            self.label = f's{AState.counter}'
            AState.counter += 1
        else:
            self.label = label

        accumulator = None
        derived = {}
        for c in configs:
            accumulator, derived = self.epsilonClosure(c, accumulator=accumulator, trace=derived)
        self.configurations = frozenset(accumulator)
        self.validLhs        = frozenset([c.clause.lhs for c in self.configurations])
        #print(f'eclose: {accumulator} {derived}')

        for k,v in derived.items():
            if isinstance(k,Grammar.TermString) or isinstance(k,Grammar.TermSet):
                barrierSrcs = barrierSources(derived,k)
                if len(barrierSrcs)>0:
                    self.byPriTerminal[k] = None
                    for b in barrierSrcs:
                        self.shiftBarriers[b] = k
                else:
                    self.byTerminal[k] = None

            # If epsilon closure expanded a nonterminal as the next symbol in a configuration then we recorded
            # symbol.name -> clause.lhs for each clause in the nonterminal's rule.
            if isinstance(k,str):
                filtered = [ entry for entry in v if isinstance(entry,Grammar.Nonterminal) ]
                if len(filtered)>0:
                    nonterminal = filtered[0].exactlyOne()
                    self.byNonterminal[nonterminal.name] = None

    def __eq__(self, other):
        return isinstance(other,AState) and self.configurations==other.configurations

    def __hash__(self):
        return hash(self.configurations)

    def __str__(self):
        return self.label

    def epsilonClosure(self, config, accumulator=None, trace=None):
        '''Process the single *config* to produce a set of derived configurations to add to the closure. Use an
           *accumulator* for the set of configurations to terminate recursion. Record the derivations in the
           *trace* so that we can infer barriers for the state.'''
        #print(f"closure: {config} {accumulator} {trace}")
        if accumulator is None:                         accumulator = set()
        if trace is None:                               trace = {}
        if config in accumulator:                       return accumulator, trace
        accumulator.add(config)
        symbol = config.next()
        if symbol is None:                              return accumulator, trace
        if symbol.modifier in ('any','optional'):
            accumulator, trace = self.epsilonClosure(config.succ(), accumulator, trace)
        if symbol.isTerminal():
            norm = symbol.exactlyOne()
            if norm not in trace:                       trace[norm] = set()
            trace[norm].add(config.clause.lhs)
            return accumulator, trace
        if not isinstance(symbol,Grammar.Nonterminal):  return accumulator, trace
        if symbol.name not in trace:                    trace[symbol.name] = set()
        trace[symbol.name].add(config.clause.lhs)
        trace[symbol.name].add(symbol)
        rule = self.grammar.rules[symbol.name]
        for clause in rule.clauses:
            initial = clause.get(0)
            accumulator, trace = self.epsilonClosure(initial, accumulator, trace)
        return accumulator, trace


class PState:
    counter = 1
    '''A state of the parser (i.e. a stack and input position). In a conventional GLR parser this would
       just be the stack, but we are building a fused lexer/parser that operates on a stream of characters
       instead of terminals.'''
    def __init__(self, stack, position, discard=None):
        self.stack = stack
        self.position = position
        self.id = PState.counter
        self.discard = discard
        PState.counter += 1

    def __hash__(self):
        return hash((tuple(self.stack),self.position))

    def __eq__(self, other):
        return isinstance(other,PState) and self.stack==other.stack and self.position==other.position

    def shifts(self, input):
        result = []
        astate = self.stack[-1]
        remaining = self.position
        for t,nextState in list(astate.byTerminal.items())+list(astate.byPriTerminal.items()):
            match = t.match(input[remaining:])
            if match is not None:
                result.append(PState(self.stack + [Automaton.Terminal(match,t),nextState],
                              remaining+len(match), discard=self.discard))
        return result

    def reductions(self):
        result = []
        astate = self.stack[-1]
        done = set()
        for handle in astate.byClause.values():
            newStack = handle.check(self.stack)
            if newStack is not None:
                #print(f'Handle match on {strs(self.stack)} => {strs(newStack)}')
                returnState = newStack[-2]
                if handle.lhs is None:
                    result.append(PState(newStack, self.position, discard=self.discard))
                    continue
                newStack.append(returnState.byNonterminal[handle.lhs])
                result.append(PState(newStack, self.position, discard=self.discard))
            #else:
            #    print(f'Handle failed on {strs(self.stack)}')
        # Must dedup as state can contain a reducing configuration that is covered by another because of repetition
        # in modifiers, i.e. x+ and xx*, or x and x*.
        return list(set(result))

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



class Automaton:
    def __init__(self, grammar):
        self.grammar       = grammar
        self.discard       = grammar.discard
        entry = Clause(None, [Grammar.Nonterminal(grammar.start)], terminating=True)
        initial = AState(grammar, [entry.get(0)], label='s0')
        self.start = initial
        worklist = OrdSet([initial])
        counter = 1

        for state in worklist:
            for edges in (state.byTerminal, state.byPriTerminal):
                for terminal in edges.keys():
                    matchingConfigs = [ c for c in state.configurations if terminal.eqOne(c.next()) ]
                    possibleConfigs = [ c.succ() for c in matchingConfigs ] + \
                                      [ c        for c in matchingConfigs if c.next().modifier in ('any','some') ]
                    assert len(possibleConfigs)>0, str(terminal)
                    next = AState(grammar, possibleConfigs, label=f's{counter}')
                    counter += 1
                    next = worklist.add(next)
                    edges[terminal] = next

            for name in list(state.byNonterminal.keys()):
                nonterminal = Grammar.Nonterminal(name)
                matchingConfigs = [ c for c in state.configurations if nonterminal.eqOne(c.next()) ]
                possibleConfigs = [ c.succ() for c in matchingConfigs ] + \
                                  [ c        for c in matchingConfigs if c.next().modifier in ('any','some') ]
                assert len(possibleConfigs)>0, str(nonterminal)
                next = AState(grammar, possibleConfigs, label=f's{counter}')
                counter += 1
                next = worklist.add(next)
                state.byNonterminal[name] = next

            for c in state.configurations:
                if c.isReducing():
                    if c.clause.hasReduceBarrier():
                        above = c.clause
                        below = c.clause.floor()
                        state.byClause[above] = Handle(above)
                        state.byPriClause[below] = Handle(below)
                        state.reduceBarriers[below] = above
                    else:
                        state.byClause[c.clause] = Handle(c.clause)

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

        print("digraph {", file=output)
        for s in self.states:
            label = "<BR/>".join([c.html() for c in s.configurations])
            print(f's{id(s)} [shape=none,label=<<font color="blue">{s.label}</font>{label} >];', file=output)

            for t,next in s.byPriTerminal.items():
                nextId = makeNextId(s, next, t, output)
                barriers = ",".join([ k.name for k,v in s.shiftBarriers.items() if v==t ])
                print(f's{id(s)} -> {nextId} [color=orange,' +
                      f'label=<<FONT color="grey">shift {t.html()}</FONT>>,' +
                      f'taillabel=<<FONT color="orange">enter {barriers}</FONT>>];', file=output)

            for t,next in s.byTerminal.items():
                nextId = makeNextId(s, next, t, output)
                print(f's{id(s)} -> {nextId} [color=grey,label=<shift {t.html()}>];', file=output)

            for nt, next in s.byNonterminal.items():
                nextId = makeNextId(s, next, nt, output)
                print(f's{id(s)} -> {nextId} [color=grey,label=<<FONT color="grey">accept {nt}</FONT>>];', file=output)

            for clause in s.byClause:
                nextId = f's{id(s)}_{id(clause)}'
                print(f'{nextId} [shape=rect,label="reduce {clause.lhs}"];', file=output)
                print(f's{id(s)} -> {nextId} [label=<{clause.html()}>];', file=output)

            for clause in s.byPriClause:
                nextId = f's{id(s)}_{id(clause)}'
                print(f'{nextId} [shape=rect,label="reduce {clause.lhs}"];', file=output)
                print(f's{id(s)} -> {nextId} [color=orange,label=<{clause.html()}>,taillabel=<<FONT color="orange">enter {clause.lhs}</FONT>>];', file=output)


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
        print("}", file=output)

    def execute(self, input, tracing=False):
        self.trace = Automaton.Trace(input, tracing)
        pstates = [PState([self.start], 0, discard=self.discard)]
        while len(pstates)>0:
            next = []
            for p in pstates:
                if not isinstance(p.stack[-1],AState):
                    if p.position==len(input) and len(p.stack)==2:
                        yield p.stack[1]
                        self.trace.result(p)
                    else:
                        self.trace.blocks(p)
                else:
                    shifts = p.shifts(input)
                    reduces = p.reductions()
                    if len(shifts)+len(reduces)==0:
                        self.trace.blocks(p)
                    else:
                        next.extend(shifts)
                        self.trace.shifts(p, shifts)
                        next.extend(reduces)
                        self.trace.reduces(p, reduces)
            pstates = next

    class Trace:
        def __init__(self, input, recording):
            self.recording = recording
            self.input     = input
            self.forwards  = MultiDict()
            self.backwards = MultiDict()

        def shifts(self, source, destinations):
            if not self.recording: return
            for d in destinations:
                self.forwards.store(source, (d, 'shift'))
                self.backwards.store(d,     (source, 'shift'))

        def reduces(self, source, destinations):
            if not self.recording: return
            for d in destinations:
                self.forwards.store(source, (d, 'reduce'))
                self.backwards.store(d,     (source, 'reduce'))

        def result(self, state):
            if not self.recording: return
            self.forwards.store(state, (True, 'emit'))
            self.backwards.store(True, (state,'emit'))

        def blocks(self, state):
            if not self.recording: return
            self.forwards.store(state, (False, 'blocks'))
            self.backwards.store(False, (state,'blocks'))

        def output(self, target):
            redundant = self.calculateRedundancy()
            print('digraph {', file=target)
            for k,v in self.forwards.map.items():
                if isinstance(k, PState):
                    for nextState, label in v:
                        fontcolor = 'black'
                        if isinstance(nextState,PState):
                            print(f's{k.id} -> s{nextState.id} [label="{label}"];', file=target)
                        else:
                            fontcolor = 'green' if nextState else 'red'
                        print(f's{k.id} [shape=none, fontcolor={fontcolor}, label={k.dotLabel(self.input,redundant[k])}];', file=target)
                else:
                    print(f'Non-pstate in trace: {repr(k)}')
            print('}', file=target)

        def calculateRedundancy(self):
            redundant = {}
            for k in self.forwards.map.keys():
                redundant[k] = True
            # The backwards map over the trace is acyclic and performance is not a concern
            def markAncestors(state):
                if not state in self.backwards.map:
                    pass #print(f'Orphan {state}')
                else:
                    for next,_ in self.backwards.map[state]:
                        redundant[next] = False
                        markAncestors(next)
            if True in self.backwards.map:
                for s,_ in self.backwards.map[True]:
                    markAncestors(s)
            return redundant

        def measure(self):
            redundant = self.calculateRedundancy().values()
            return len([v for v in redundant if v]) / len(redundant)


    class Terminal:
        def __init__(self, chars, original):
            self.chars    = chars
            self.original = original
            self.tag = original.tag

        def __str__(self):
            return self.chars

        def matches(self, other):
            return type(other) in (Grammar.TermString, Grammar.TermSet) and other.match(self.chars)

        def dump(self, depth=0):
            print(f"{'  '*depth}{self.chars}")

    class Nonterminal:
        def __init__(self, tag, children ):
            self.tag      = tag
            self.children = tuple(children)
            for c in self.children:
                assert isinstance(c,Automaton.Terminal) or isinstance(c,Automaton.Nonterminal), repr(c)

        def __str__(self):
            return str(self.tag)

        def __eq__(self, other):
            return isinstance(other,Parser.Nonterminal) and self.tag==other.tag and self.children==other.children

        def __hash__(self):
            return hash((self.tag,self.children))

        def matches(self, other):
            return isinstance(other,Grammar.Nonterminal) and self.tag == other.name

        def dump(self, depth=0):
            print(f"{'  '*depth}{self.tag}")
            for c in self.children:
                c.dump(depth+1)

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
