# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .util import MultiDict, OrdSet
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

