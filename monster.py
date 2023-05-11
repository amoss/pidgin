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
        body = [ symbol for symbol in initialBody ]
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


class Grammar:
    def __init__(self, start):
        self.rules    = dict()
        self.start    = start
        self.discard  = None

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
        def __init__(self, match, modifier="just", tag='', original=None):
            '''A terminal symbol that matches a string literal *match*. If the *modifier* is repeating then
               the match is always greedy. If non-greedy matching is required then it can be simulated by
               wrapping in a non-terminal (with glue if appropriate).'''
            self.string = match
            self.tag = tag
            assert modifier in ("any","just","some","optional"), modifier
            self.modifier = modifier
            self.strength = 'greedy'
            self.original = self if original is None else original

        def __str__(self):
            tag = f",{self.tag}" if self.tag!="" else ""
            return f"T({repr(self.string)},{self.modifier}{tag})"


    class TermSet:
        def __init__(self, charset, modifier="just", inverse=False, tag='', original=None):
            assert modifier in ("any","just","some","optional"), modifier
            self.modifier = modifier
            self.strength = "greedy"
            self.chars = frozenset(charset)
            self.inverse  = inverse
            self.tag      = tag
            self.original = self if original is None else original

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


    class Nonterminal:
        def __init__(self, name, strength="greedy", modifier="just"):
            assert modifier in ("any", "just", "some", "optional"), modifier
            assert strength in ("all", "frugal", "greedy"), strength
            self.name     = name
            self.modifier = modifier
            self.strength = strength

        def __str__(self):
            return f"N({self.strength},{self.modifier},{self.name})"

    class Glue:
        def __init__(self):
            self.within = None
            self.position = None
            self.modifier = "just"
            self.strength = "greedy"

        def __str__(self):
            return "Glue"

    class Remover:
        def __init__(self):
            self.within = None
            self.position = None
            self.modifier = "just"
            self.strength = "greedy"

        def __str__(self):
            return "Remover"


class Handle:
    def __init__(self, config):
        '''Build a restricted NFA for recognising the configuration - no loops larger than self-loops, no choices.
           The NFA is a straight-line with self-loops on repeating nodes and jumps over skipable nodes.
           Translate the NFA to a DFA that we store / use for recognition. The recogniser works in reverse so that
           we can scan down the stack.'''
        nfaStates  = list(reversed([s for s in config.rhs if s.isTerminal() or s.isNonterminal()]))
        nfaSkips   = [ s.modifier in ('optional','any') for s in nfaStates ] + [False]
        nfaRepeats = [ s.modifier in ('some','any') for s in nfaStates ]     + [False]
        nfaEdges   = [ MultiDict() for i in range(len(nfaStates)) ]          + [MultiDict()]

        for i,s in enumerate(nfaStates):
            if nfaRepeats[i]:
                nfaEdges[i].store(s.eqClass, i)
            for tar in range(i+1,len(nfaStates)+2):
                nfaEdges[i].store(s.eqClass, tar)
                if not nfaSkips[tar]:
                    break

        initial = []
        for i in range(len(nfaStates)+1):
            initial.append(i)
            if not nfaSkips[i]:
                break
        self.initial = frozenset(initial)
        self.exit = len(nfaStates)
        self.lhs = config.lhs

        def successor(dfaState, eqClass):
            result = set()
            for nfaIdx in dfaState:
                if eqClass in nfaEdges[nfaIdx].map:
                    result.update(nfaEdges[nfaIdx].map[eqClass])
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
            for eqClass in ogEdges(state):
                succ = successor(state, eqClass)
                self.dfa.store(state, (eqClass,succ))
                worklist.add(succ)

    def check(self, stack):
        '''Check the stack against the DFA. If we find a match then return the remaining stack after the
           handle has been removed.'''
        assert isinstance(stack[-1], AState), f'Not an AState on top {stack[-1]}'
        assert (len(stack)%2) == 1, f'Even length stack {strs(stack)}'
        pos = len(stack)-2
        dfaState = self.initial
        #print(f'check: {self.dfa.map}')
        while pos>0:
            next = None
            if dfaState in self.dfa.map:   # If dfaState = { nfaExit } then it won't be in the edge map
                for symbol, succ in self.dfa.map[dfaState]:
                    if stack[pos].symbol==symbol and self.lhs in stack[pos-1].validLhs:
                        next = succ
                        pos -= 2
                        break
            if next is None:
                if self.exit in dfaState:
                    onlySymbols = ( s for s in stack[pos+2:] if not isinstance(s,AState) )
                    return stack[:pos+2] + [Token(self.lhs,onlySymbols)]
                return None
            dfaState = next
        if self.exit in dfaState:
            onlySymbols = ( s for s in stack[pos+2:] if not isinstance(s,AState) )
            return stack[:pos+2] + [Token(self.lhs,onlySymbols)]
        return None

    def __str__(self):
        res = ""
        for k,v in self.dfa.map.items():
            res += ",".join([str(state) for state in k]) + ':['
            res += " ".join([str(term) + '->' + ",".join([str(state) for state in target]) for (term,target) in v])
            res += ']'
        return res


    '''In order to terminate the recursion at a fixed-point within the epsilon-closure we have
       contructed path-fragments that cover the set of paths within the closure. In order to
       use them to define the priority of edges originating at the state we need to perform a
       step similar to the pumping lemma on the fragments to reconstruct a minimal set of
       paths that we can measure the priorities on (by scanning the priority markers on the
       reconstructed paths).'''



class EpsilonRecord:
    def __init__(self, grammar, initialConfigs):
        self.grammar  = grammar
        self.internal = {}
        self.exit     = {}
        self.accept   = set()
        self.initial  = frozenset(initialConfigs)
        for c in initialConfigs:
            self.closure(c)


    def closure(self, config):
        if config in self.internal:
            return
        self.internal[config] = set()
        self.exit[config]     = set()
        symbol = config.next()
        if symbol is None:
            self.exit[config].add( (None,config) )
        else:
            todo = []
            if symbol.modifier in ('any','optional'):
                self.internal[config].add( ('lo',config.succ()) )
                todo.append(config.succ())
                pri = 'hi'
            else:
                pri = None

            if symbol.isNonterminal():
                for ntInitial in self.grammar[symbol.eqClass.name]:
                    self.internal[config].add( (pri,ntInitial) )
                    todo.append(ntInitial)
                self.accept.add(symbol.eqClass)
            else:
                self.exit[config].add( (pri,symbol.eqClass) )

            for c in todo:
                self.closure(c)


    def configs(self):
        return frozenset(self.internal.keys())


    def paths(self):
        def prepend(priority, seq):
            if priority is not None:
                return (priority,)+seq
            return seq

        def followPath(node, marked):
            result = set()
            marked = marked | set([node])
            for (priority,symbol) in self.exit[node]:
                result.add( prepend(priority, (symbol,)) )
            for (priority,next) in self.internal[node]:
                if next not in marked:
                    for p in followPath(next, marked):
                        result.add( prepend(priority,p) )
            return result

        def normalize(seq):
            symbol = seq[-1]
            markers = seq[:-1]
            # Treat the path markers as fractional binary strings to project onto a set that preserves ordering.
            # This is correct as long as the mantissa in the sum does not overflow, which will occur if there is
            # a chain of priority-relevant non-terminals longer than 53 in the epsilon closure. So... don't make
            # grammars that do that :)
            radix = 1.
            if len(markers)==0:
                sum = -1.
            else:
                sum = 0.
                for pri in markers:
                    if pri=="hi":
                        sum += radix
                    radix = radix / 2.0
            return (sum,symbol)

        def removeShadows(pairs):
            if len(pairs)<2:
                return pairs
            return pairs[:1] + removeShadows([p for p in pairs[1:] if p[1]!=pairs[0][1] ])

        allResults = set()
        for seed in self.initial:
            allResults.update( normalize(p) for p in followPath(seed, marked=set()) )
        noncontiguous = list(allResults)
        noncontiguous.sort(key=lambda pair:pair[0], reverse=True)
        noncontiguous = removeShadows(noncontiguous)
        contiguous = list(enumerate([ symbols for pri,symbols in noncontiguous ]))
        print(contiguous)
        return contiguous


# TODO:
#       quoted_str2: fails because we don't try lower pri when barriered region fails
#       recurse_degenseq3:  non-deterministic failure. This is the one with the free reduction to
#                           R on an empty string at the beginning of the trace. Looks like the shift
#                           fromt he second state should not be lower priority than the reduce?
#       recurse_termplusvianonterm: non-deterministic failure on p0, p1-p3 always fail
#                                   The order of the three reductions from the second state should work when
#                                   we have failure on the barriered region.
#       regex_selfalignboundedright2: non-deterministic failure
#       pidgin_term: blocks on the >> sequence, same problem as quoted_str2


class AState:
    counter = 1
    '''A state in the LR(0) automaton'''
    def __init__(self, grammar, configs, label=None):
        assert len(configs)>0
        self.grammar = grammar
        self.edges = [{}]
        if label is None:
            self.label = f's{AState.counter}'
            AState.counter += 1
        else:
            self.label = label

        #print(f'{self.label}:')
        record = EpsilonRecord(grammar, configs)
        self.configurations = record.configs()
        self.validLhs        = frozenset([c.lhs for c in self.configurations])
        contiguous = record.paths()

        nonterminals = set()
        for pri,symbol in contiguous:
            self.addEdge(pri, symbol, None)
        for symbol in record.accept:
            self.addEdge(0, symbol, None)           # TODO: Hmmm, so many questions????

    def addEdge(self, priority, eqClass, target):
        while priority >= len(self.edges):
            self.edges.append({})
        self.edges[priority][eqClass] = target

    def __eq__(self, other):
        return isinstance(other,AState) and self.configurations==other.configurations

    def __hash__(self):
        return hash(self.configurations)

    def __str__(self):
        return self.label

        '''Process the single *config* to produce a set of derived configurations to add to the closure. Use
           the next symbol in the *config* to decide on how to expand the closure, terminals are recorded in
           the traces accumulated in traceAcc. Non-terminals are looked up in the grammar to add their
           initial configurations to the accumulator *configAcc*. The accumulators are used to terminate on
           the least fixed-point. Where looping modifiers cause a divergence in the chain of symbols insert
           textual markers into the *prefix* trace to indicate the priority of each path. These will be
           reconstructed into the edge-priority for the state.'''

class Barrier:
    counter = 1
    def __init__(self, continuation):
        self.states = set()
        self.continuation = continuation
        self.id = Barrier.counter
        Barrier.counter += 1

    def register(self, state):
        assert state.barrier is None,\
               f"Register in {self.id} but already inside barrier {state.barrier.id} for p{state.id}"
        state.barrier = self
        self.states.add(state)

    def cancel(self):
        for state in self.states:
            state.barrier = None
        self.states = set()
        self.continuation = []

    def complete(self, state):
        #print(f'b{self.id}: {self.states} - {state}')
        self.states.remove(state)
        if len(self.states)==0:
            return self.continuation

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
        self.barrier        = None
        if barrier is not None:
            barrier.register(self)
        PState.counter += 1

    def __hash__(self):
        return hash((tuple(self.stack),self.position))

    def __eq__(self, other):
        return isinstance(other,PState) and self.stack==other.stack and self.position==other.position

    def register(self, barrier):
        if barrier is not None:
            barrier.register(self)

    def cancel(self):
        if self.barrier is not None:
            self.barrier.cancel()

    def complete(self):
        if self.barrier is not None:
            return self.barrier.complete(self)

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
        barrier = f'<font color="orange">b{self.barrier.id}</font>' if self.barrier is not None else ''
        if not isinstance(astate,AState):
            return "<Terminated>"
        if len(remaining)>30:
            result =  f'< <table border="0"><tr><td{cell}>{barrier}{html.escape(remaining[:30])}...</td></tr><hr/>'
        else:
            result =  f'< <table border="0"><tr><td{cell}>{barrier}{html.escape(remaining)}</td></tr><hr/>'

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

class Token:
    def __init__(self, symbol, content):
        self.symbol   = symbol
        self.contents = content

    def __str__(self):
        if self.symbol is not None and self.symbol.isTerminal:
            return f'{self.symbol}:{self.contents}'
        return f'{self.symbol}::'

    def dump(self, depth=0):
        print(f"{'  '*depth}{self.tag}")
        for c in self.children:
            c.dump(depth+1)



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
                print(f'Execute p{p.id} {strs(p.stack)}')
                if p.barrier is not None:
                    self.trace.barrier(p,p.barrier)
                if not isinstance(p.stack[-1],AState):
                    remaining = p.position + self.processDiscard(input[p.position:])
                    if remaining==len(input) and len(p.stack)==2:
                        yield p.stack[1]
                        p.cancel()
                        self.trace.result(p)
                    else:
                        self.trace.blocks(p)
                else:
                    #try:
                    succ = p.successors(input)
                    print(f'succ {[st.id for pri in succ for st in pri ]}')
                    if len(succ)==0:
                        self.trace.blocks(p)
                    else:
                        barrier = None
                        if len(succ)>1:
                            barrier = Barrier(succ[1:])

                        for state in succ[0]:
                            if state.label=="shift":
                                self.trace.shift(p,state)
                            else:
                                self.trace.reduce(p,state)
                            next.append(state)
                            state.register(barrier)
                    #except AssertionError as e:
                    #    self.trace.blocks(p)
                    #    print(f'ERROR {e}')
                    continuation = p.complete()
                    if continuation is not None:
                        barrier = None
                        if len(continuation)>1:
                            barrier = Barrier(continuation[1:])

                        for state in continuation[0]:
                            if state.label=="shift":
                                self.trace.shift(p.barrier,state)
                            else:
                                self.trace.reduce(p.barrier,state)
                            next.append(state)
                            state.register(barrier)

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
            self.forwards.store(source,  (destination, 'shift'))
            self.backwards.store(destination, (source, 'shift'))

        def reduce(self, source, destination):
            if not self.recording: return
            self.forwards.store(source,  (destination, 'reduce'))
            self.backwards.store(destination, (source, 'reduce'))

        def result(self, state):
            if not self.recording: return
            self.forwards.store(state, (True, 'emit'))
            self.backwards.store(True, (state,'emit'))

        def blocks(self, state):
            if not self.recording: return
            self.forwards.store(state, (False, 'blocks'))
            self.backwards.store(False, (state,'blocks'))

        def barrier(self, source, destination):
            if not self.recording: return
            self.forwards.store(source,  (destination, 'barrier'))
            self.backwards.store(destination, (source, 'barrier'))


        def output(self, target):
            self.calculateRedundancy()
            print('digraph {', file=target)
            for k,v in self.forwards.map.items():
                if isinstance(k, PState):
                    for nextState, label in v:
                        fontcolor = 'black'
                        if isinstance(nextState,PState):
                            print(f's{k.id} -> s{nextState.id} [label="{label}"];', file=target)
                        elif isinstance(nextState,Barrier):
                            print(f's{k.id} -> b{nextState.id} [label="inside",color=orange,fontcolor=orange];', file=target)
                        else:
                            fontcolor = 'green' if nextState else 'red'
                    print(f's{k.id} [shape=none, fontcolor={fontcolor}, '+
                          f'label={k.dotLabel(self.input,self.redundant[k])}];', file=target)
                elif isinstance(k, Barrier):
                    for nextState, label in v:
                        print(f'b{k.id} -> s{nextState.id} [label="continues",color=orange,fontcolor=orange];', file=target)
                    print(f'b{k.id} [shape=none, fontcolor=orange, label="Barrier {k.id}"];', file=target)
                else:
                    print(f'Non-pstate in trace: {repr(k)}')
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
