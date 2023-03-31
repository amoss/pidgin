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

    def addRule(self, name, body):
        assert not name in self.rules.keys()
        rule = Rule(name, self)
        rule.add(body)
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
            '''The *modifier* applies to matching the *charset* within a single symbol, in contrast
               to how the modifier works on non-terminals.'''
            assert modifier in ("any","just","some","optional"), modifier
            self.internal = "some" if modifier in ("any","some") else "just"
            self.modifier = "optional" if modifier in ("optional","any") else "just"
            self.orig = modifier
            self.chars = frozenset(charset)
            self.inverse  = inverse
            self.tag      = tag

        def __str__(self):
            if len(self.chars)<=5:
                charset = ",".join([c if c!=',' else "','" for c in self.chars])
            else:
                charset = ",".join([c if c!=',' else "','" for c in list(self.chars)[:5]]) + f' +{len(self.chars)-5}'
            if self.inverse:
                result = 'T(^{"' + charset + '},'
            else:
                result = 'T({"' + charset + '},'
            tag = f",{self.tag}" if self.tag!="" else ""
            return f'{result},{self.orig}{tag})'

        def html(self):
            return '[]'

        def sig(self):
            return (self.chars, self.modifier, self.inverse, self.tag)

        def __eq__(self,other):
            return isinstance(other,Grammar.TermSet) and self.sig()==other.sig()

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
            limit = len(input) if self.internal in ("any","some") else 1
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

class AState:
    '''A state in the LR(0) automaton'''
    def __init__(self, grammar, configs):
        self.grammar = grammar
        self.byPriTerminal   = {}
        self.shiftBarriers   = {}
        self.byTerminal      = {}
        self.byNonterminal   = {}
        self.byClause        = set()
        self.byPriClause     = set()
        self.reduceBarriers  = {}

        accumulator = None
        derived = {}
        for c in configs:
            accumulator, derived = self.epsilonClosure(c, accumulator=accumulator, trace=derived)
        self.configurations = frozenset(accumulator)
        print(f'eclose: {accumulator} {derived}')

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
                    self.byNonterminal[nonterminal] = None




#        self.byGlue = {}
#        self.byRemover = {}


    def __eq__(self, other):
        return isinstance(other,AState) and self.configurations==other.configurations

    def __hash__(self):
        return hash(self.configurations)

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
        if symbol.modifier in ('any','optional'):
            accumulator, trace = self.epsilonClosure(config.succ(), accumulator, trace)
        return accumulator, trace

    def connectShift(self, terminal, next):
        pass

    def connectPriShift(self, terminal, exit, next):
        pass



    def connect(self, symbol, next, repeats=False):
        assert type(symbol) in (Grammar.TermSet, Grammar.TermString, Grammar.Nonterminal, Grammar.Glue, 
                                Grammar.Remover), symbol
        assert isinstance(next,AState), next
        if symbol.isTerminal():
            self.byTerminal[symbol] = next
            self.repeats[symbol] = repeats
        elif isinstance(symbol, Grammar.Glue):
            self.byGlue[symbol] = next
        elif isinstance(symbol, Grammar.Remover):
            self.byRemover[symbol] = next
        else:
            self.byNonterminal[symbol.name] = next
            self.repeats[symbol.name] = repeats

    def addReducer(self, clause):
        self.byClause.add(clause)


class Automaton:
    def __init__(self, grammar):
        self.grammar       = grammar
        self.discard       = grammar.discard
        entry = Clause(None, [Grammar.Nonterminal(grammar.start)], terminating=True)
        initial = AState(grammar, [entry.get(0)])
        self.start = initial
        worklist = OrdSet([initial])

        for state in worklist:
            for edges in (state.byTerminal, state.byPriTerminal):
                for terminal in edges.keys():
                    possibleConfigs = [ c.succ() for c in state.configurations if c.next()==terminal ]
                    next = AState(grammar, possibleConfigs)
                    next = worklist.add(next)
                    edges[terminal] = next

            for nonterminal in state.byNonterminal.keys():
                eqRepeating = lambda sym: isinstance(sym,Grammar.Nonterminal) and \
                                          sym.modifier in ('any','some') and      \
                                          sym.name==nonterminal.name
                possibleConfigs  = [ c.succ() for c in state.configurations if c.next()==nonterminal ]
                possibleConfigs += [ c        for c in state.configurations if eqRepeating(c.next()) ]
                next = AState(grammar, possibleConfigs)
                next = worklist.add(next)
                state.byNonterminal[nonterminal] = next

            for c in state.configurations:
                if c.isReducing():
                    if c.clause.hasReduceBarrier():
                        above = c.clause
                        below = c.clause.floor()
                        state.byClause.add(above)
                        state.byPriClause.add(below)
                        state.reduceBarriers[below] = above
                    else:
                        state.byClause.add(c.clause)

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
            print(f's{id(s)} [shape=none,label=< {label} >];', file=output)

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
                nextId = makeNextId(s, next, t, output)
                print(f's{id(s)} -> {nextId} [color=grey,label=<<FONT color="grey">accept {nt.name}</FONT>>];', file=output)

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




#g = Grammar('E')
#E = g.addRule('E',[g.TermString('x'), g.Nonterminal('E2', strength='greedy', modifier='any')])
#E.add(            [g.TermString('<'), g.Nonterminal('E'), g.TermString('>'), g.Nonterminal('E2', strength='greedy', modifier='any')])
#g.addRule('E2',   [g.TermString('+'), g.Nonterminal('E')])

#g = Grammar('R')
#g.addRule('R', [g.Nonterminal('R', modifier='any', strength='greedy'), g.TermString('x') ])

#g = Grammar('P')
#P = g.addRule('P', [g.Nonterminal('U', modifier='any', strength='greedy'), g.TermString('z')])
#P.add(             [g.Nonterminal('V', modifier='any', strength='greedy'), g.TermString('k')])
#U = g.addRule('U', [g.TermString('x')])
#U.add(             [g.TermString('y')])
#V = g.addRule('V', [g.TermString('x')])
#V.add(             [g.TermString('y')])
#a = Automaton(g)
#a.dot(open("t.dot","wt"))
#
#
