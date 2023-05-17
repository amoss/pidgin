# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import html

from .util import MultiDict, OrdSet
from .grammar import Clause, Grammar


class EpsilonRecord:
    '''A record of how the epsilon-closure was calculated on an AState. The closure defines which
       symbols may be accepted next in the AState, and retracing the steps used to add configurations
       to the closure allows calculation of the symbol priority.'''
    def __init__(self, grammar, initialConfigs):
        self.grammar  = grammar
        self.internal = {}
        self.exit     = {}
        self.accept   = set()
        self.initial  = frozenset(initialConfigs)
        for c in initialConfigs:
            self.closure(c)


    def closure(self, config):
        '''Process the single *config* to produce a set of derived configurations to add to the closure. Use
           the next symbol in the *config* to decide on how to expand the closure. Non-terminals are looked
           up in the grammar to add their initial configurations. Each next symbol can be viewed as an edge
           in a DAG that holds the configurations in the closure. These edges are partitioned into thei
           *internal* and *exit* collections as the record.'''
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

        def repack(pairs):
            '''Convert the non-contiguous (but ordered) priorites into a contiguous numbering.'''
            currentPri, path = pairs[0]
            densePri = 0
            result = [(densePri,path)]
            for pri, path in pairs[1:]:
                if pri!=currentPri:
                    densePri = 1
                currentPri = pri
                result.append( (densePri, path) )
            return result

        allResults = set()
        for seed in self.initial:
            allResults.update( normalize(p) for p in followPath(seed, marked=set()) )
        noncontiguous = list(allResults)
        noncontiguous.sort(key=lambda pair:pair[0], reverse=True)
        noncontiguous = removeShadows(noncontiguous)
        contiguous = repack(noncontiguous)
        return contiguous


class AState:
    counter = 1
    '''A state (collection of configurations) in the LR(0) automaton'''
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
            self.addEdge(0, symbol, None)

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
        '''Check the stack against the DFA. If we find a match then split the stack to return the new stack
           and the handle with AStates filtered out.'''
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
                    return stack[:pos+2], onlySymbols
                return None, None
            dfaState = next
        if self.exit in dfaState:
            onlySymbols = ( s for s in stack[pos+2:] if not isinstance(s,AState) )
            return stack[:pos+2], onlySymbols
        return None, None


    def __str__(self):
        res = ""
        for k,v in self.dfa.map.items():
            res += ",".join([str(state) for state in k]) + ':['
            res += " ".join([str(term) + '->' + ",".join([str(state) for state in target]) for (term,target) in v])
            res += ']'
        return res


class Symbol:
    '''A symbol is a unit of matching in a grammar (either a terminal from the alphabet or a non-terminal
       covering a sequence of terminals), or a special symbol that alters the glue-state / discard-channel
       in the parser. Raw symbols in the initial grammar are represented by inner classes of Grammar. These
       symbols exist after canonicalization calculates the equivalence classes, and are used in Configurations
       of the machine and wrapped in Tokens for the stack during a parse.'''
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

