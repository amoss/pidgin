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
            elif isinstance(s,Grammar.Glue):
                result += '<FONT color="grey"><B>G</B></FONT>'
            elif isinstance(s,Grammar.Remover):
                result += '<FONT color="grey"><B>R</B></FONT>'
            else:
                result += type(s).__name__ + modifier
        return result

    def isTerminal(self):
        return False

    #def get(self, position):
    #    if self.configs[position] is None:
    #        self.configs[position] = Configuration(self, position)
    #    return self.configs[position]


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
            return Grammar.TermString(self.string, modifier="just", tag=self.tag, original=self.original)

        # Does this still get used or is it dead?
        #def order(self):
        #    return (0, 1, self.string)

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

        def html(self):
            return '[]'

        def sig(self):
            return (self.chars, self.modifier, self.inverse, self.tag, id(self.original))

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
            return Grammar.TermSet(self.chars, modifier="just", inverse=self.inverse, tag=self.tag, original=self.original)

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
            self.strength = "greedy"

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
            self.strength = "greedy"

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


class AState:
    counter = 1
    '''A state in the LR(0) automaton'''
    def __init__(self, grammar, configs, label=None):
        assert len(configs)>0
        self.grammar = grammar

        self.edges = [{}]
        print(f'AState({strs(configs)})')

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
        self.validLhs        = frozenset([c.lhs for c in self.configurations])
        #print(f'eclose: {accumulator} {derived}')

        priority = 0
        for k,v in derived.items():
            #print(f'construct {self.label} entry {k} {type(k)} : {v}')
            if isinstance(k, SymbolTable.TermSetEQ) or isinstance(k, SymbolTable.TermStringEQ):
                barrierSrcs = barrierSources(derived,k)
                self.addEdge(priority, k, None)
            # If epsilon closure expanded a nonterminal as the next symbol in a configuration then we recorded
            # symbol.name -> clause.lhs for each clause in the nonterminal's rule.
            if isinstance(k,str):
                filtered = set([ entry.eqClass for entry in v if isinstance(entry,Symbol) and entry.isNonterminal() ])
                assert len(filtered) in (0,1), filtered
                if len(filtered)>0:
                    self.addEdge(0, list(filtered)[0], None)

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
            if symbol.eqClass not in trace:             trace[symbol.eqClass] = set()
            trace[symbol.eqClass].add(config.lhs)
            return accumulator, trace
        if not symbol.eqClass.isNonterminal:            return accumulator, trace
        name = symbol.eqClass.name
        if name not in trace:                           trace[name] = set()
        trace[name].add(config.lhs)
        trace[name].add(symbol)
        for ntInitialConfig in self.grammar[name]:
            accumulator, trace = self.epsilonClosure(ntInitialConfig, accumulator, trace)
        return accumulator, trace


class PState:
    counter = 1
    '''A state of the parser (i.e. a stack and input position). In a conventional GLR parser this would
       just be the stack, but we are building a fused lexer/parser that operates on a stream of characters
       instead of terminals.'''
    def __init__(self, stack, position, keep=False, discard=None):
        self.stack = stack
        self.position = position
        self.id = PState.counter
        self.discard = discard
        self.keep = keep
        PState.counter += 1

    def __hash__(self):
        return hash((tuple(self.stack),self.position))

    def __eq__(self, other):
        return isinstance(other,PState) and self.stack==other.stack and self.position==other.position

    def successors(self, input):
        result = []
        astate = self.stack[-1]
        remaining = self.position
        if not self.keep and self.discard is not None:
            drop = self.discard.match(input[remaining:])
            if drop is not None and len(drop)>0:
                remaining += len(drop)
        #print(f'execute: {strs(self.stack)}')
        for priLevel in astate.edges:
            for edgeLabel,target in priLevel.items():
                #print(f'edge: {edgeLabel} target: {target}')
                if isinstance(edgeLabel, Automaton.Configuration) and isinstance(target,Handle):
                    newStack = target.check(self.stack)
                    #print(f'newStack={newStack}')
                    if newStack is not None:
                        #print(f'Handle match on old {strs(self.stack)}')
                        #print(f'                 => {strs(newStack)}')
                        if target.lhs is None:
                            result.append(("reduce",PState(newStack, self.position, discard=self.discard, keep=self.keep)))
                            continue
                        returnState = newStack[-2]
                        assert target.lhs in returnState.edges[0], \
                               f'Missing {target.lhs} in {returnState.label} after {strs(newStack)}'
                        newStack.append(returnState.edges[0][edgeLabel.lhs])
                        result.append( ("reduce",PState(newStack, self.position, discard=self.discard, keep=self.keep)))
                elif isinstance(edgeLabel, SymbolTable.SpecialEQ) and edgeLabel.name=="glue":
                    result.append( ("shift",PState(self.stack[:-1] + [target], self.position, discard=self.discard, keep=True)))
                elif isinstance(edgeLabel, SymbolTable.SpecialEQ) and edgeLabel.name=="remover":
                    result.append( ("shift",PState(self.stack[:-1] + [target], remaining, discard=self.discard, keep=False)))
                else:
                    assert type(edgeLabel) in (SymbolTable.TermSetEQ,
                                               SymbolTable.TermStringEQ,
                                               SymbolTable.NonterminalEQ), type(edgeLabel)
                    if len(input)>remaining:
                        matched = edgeLabel.matchInput(input[remaining:])
                        if matched is not None:
                            result.append( ("shift",PState(self.stack + [Token(edgeLabel,matched),target],
                                                           remaining+len(matched),
                                                           discard=self.discard, keep=self.keep)))
            if len(result)>0:
                break
        return result

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
                cons = lambda: SymbolTable.TermSetEQ(s.chars)
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
        def __init__(self, chars):
            self.chars = chars
        def __str__(self):
            return f'[{self.index}]'
        def html(self, modifier=''):
            return f'<FONT face="monospace">[{self.index}]</FONT>{modifier}'
        def isTerminal(self):
            return True
        def isNonterminal(self):
            return False
        def matchInput(self, input):
            if input[0] in self.chars:
                return input[:1]
            return None
        #def createInstance(self):
        #    return Symbol(
        #    ...

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
            if input[:len(self.literal)]==self.literal:
                return self.literal
            return None
        #def createInstance(self):
            ...

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
        #def createInstance(self):

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

    def dump(self, depth=0):
        print(f"{'  '*depth}{self.tag}")
        for c in self.children:
            c.dump(depth+1)



class Automaton:

    # Are these classes or instances???
    # AState edges: classes
    # DFA edges: classes
    # Stack entries: instances
    class Configuration:
        def __init__(self, lhs, rhs, position=0):
            self.lhs      = lhs
            self.rhs      = tuple(rhs)
            self.position = position

        def __str__(self):
            return f'{self.lhs} <- ' + " ".join(['^'+str(s) if self.position==i else str(s)
                                                            for i,s in enumerate(self.rhs)])
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
            for c in s:
                print(c)


    def __init__(self, grammar):

        self.canonicalizeGrammar(grammar)
        #self.grammar       = grammar
        self.discard       = grammar.discard

        entry = Automaton.Configuration(None, self.symbolTable.canonSentence([Grammar.Nonterminal(grammar.start)])) # terminating?
        initial = AState(self.canonGrammar, [entry], label='s0')
        self.start = initial
        worklist = OrdSet([initial])
        counter = 1

        for state in worklist:
            active = [c for c in state.configurations if c.next() is not None ]
            for pri, priLevel in enumerate(state.edges):
                for eqClass in priLevel.keys():
                    if eqClass.isTerminal or eqClass.isNonterminal:
                        matchingConfigs = [ c for c in active if c.next().eqClass==eqClass ]
                        possibleConfigs = [ c.succ() for c in matchingConfigs ] + \
                                          [ c        for c in matchingConfigs if c.next().modifier in ('any','some') ]
                        assert len(possibleConfigs)>0, str(eqClass)
                        next = AState(self.canonGrammar, possibleConfigs, label=f's{counter}')
                        counter += 1
                        next = worklist.add(next)
                        priLevel[eqClass] = next

            for special in ("glue","remover"):
                withSpecial = [ c for c in active
                                  if isinstance(c.next().eqClass, SymbolTable.SpecialEQ) and c.next().eqClass.name==special ]
                if len(withSpecial)>0:
                    next = AState(grammar, [c.succ() for c in withSpecial], label=f's{counter}')
                    counter += 1
                    next = worklist.add(next)
                    state.addEdge(0, withSpecial[0].next().eqClass, next)

            for c in state.configurations:
                if c.isReducing():
                    state.addEdge(0, c, Handle(c))
                    if c.hasReduceBarrier():
                        below = c.floor()
                        state.addEdge(1, below, Handle(below))

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
                            print(f's{id(s)} -> {nextId} [label=<edgeLabel.html()>];', file=output)
        print("}", file=output)

    def execute(self, input, tracing=False):
        self.trace = Automaton.Trace(input, tracing)
        pstates = [PState([self.start], 0, discard=self.discard)]
        while len(pstates)>0:
            next = []
            for p in pstates:
                if not isinstance(p.stack[-1],AState):
                    remaining = p.position
                    if not p.keep and self.discard is not None:
                        drop = self.discard.match(input[remaining:])
                        if drop is not None and len(drop)>0:
                            remaining += len(drop)
                    if remaining==len(input) and len(p.stack)==2:
                        yield p.stack[1]
                        self.trace.result(p)
                    else:
                        self.trace.blocks(p)
                else:
                    try:
                        succ = p.successors(input)
                        if len(succ)==0:
                            self.trace.blocks(p)
                        else:
                            for label,state in succ:
                                if label=="shift":
                                    self.trace.shift(p,state)
                                else:
                                    self.trace.reduce(p,state)
                                next.append(state)
                    except AssertionError as e:
                        self.trace.blocks(p)
                        print(f'ERROR {e}')

            pstates = next

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

        def output(self, target):
            self.calculateRedundancy()
            print('digraph {', file=target)
            for k,v in self.forwards.map.items():
                if isinstance(k, PState):
                    for nextState, label in v:
                        fontcolor = 'black'
                        if isinstance(nextState,PState):
                            print(f's{k.id} -> s{nextState.id} [label="{label}"];', file=target)
                        else:
                            fontcolor = 'green' if nextState else 'red'
                        print(f's{k.id} [shape=none, fontcolor={fontcolor}, '+
                              f'label={k.dotLabel(self.input,self.redundant[k])}];', file=target)
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
