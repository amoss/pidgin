# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

import itertools
import math
import random
from bootstrap.grammar import Grammar
from bootstrap.interpreter import buildCommon, stage2
from bootstrap.util import strs


def ordered_partitions_n(total, length):
    if length==0:
        yield []
    elif length==1:
        yield [total]
    else:
        for i in range(total+1):
            for suffix in ordered_partitions_n(total-i,length-1):
                yield [i] + suffix

def ordered_binary_partitions_below_n(total, length):
    if length==0:
        yield []
    elif length==1:
        yield [0]
        if total>=1:
            yield [1]
    else:
        for i in range(min(1,total)+1):
            for suffix in ordered_binary_partitions_below_n(total-i,length-1):
                yield [i] + suffix


class Sampler:
    def __init__(self, grammar):
        self.grammar = grammar
        self.memo    = {}

    def uniform(self, ruleName, size):
        rule = self.grammar.rules[ruleName]
        choices = [ (clause, self.count_clause(clause,size))  for clause in rule.clauses ]
        print(choices)

    def count_rule(self, ruleName, size):
        rule = self.grammar.rules[ruleName]
        im = [self.count_clause(clause,size) for clause in rule.clauses]
        print(ruleName,im)
        return sum(im)
        #return sum( self.count_clause(clause,size) for clause in rule.clauses)

    def count_nonterminal(self, symbol, size):
        if symbol.modifier=="just":
            return self.count_rule(symbol.name,size)
        if symbol.modifier=="any":
            if size==0:  return 1
            combinations = 0
            for prefix in range(1,size+1):
                combinations += self.count_rule(symbol.name,prefix) * self.count_nonterminal(symbol, size-prefix)
            return combinations
        if symbol.modifier=="some":
            if size==0:  return 0
            combinations = 0
            suffixSymbol = symbol.copy()
            suffixSymbol.modifier = "any"
            for prefix in range(1,size+1):
                combinations += self.count_rule(symbol.name,prefix) * self.count_nonterminal(suffixSymbol, size-prefix)
            return combinations
        if symbol.modifier=="optional":
            if size==0:  return 1
            return self.count_rule(symbol.name,size)
        assert False

    # Different lists of expansion coefficents, for terminals
    #   exact      - terminals "just"
    #   zeroMore   - terminals "any" -> can treat same as nonterms?
    #   oneMore    - could put one in exact, remainder in zeroMore?
    #   zeroOne    - combinations of 0/1 in separate generator...
    # Then for nonterms
    #   "just" -> existing processing
    #   "optional" -> modify existing to count zero separately
    #   "any" -> ? include sequences in count
    #   "some" -> ??

    def count_clause(self, clause, size):
        terminals = [s for s in clause.rhs if s.isTerminal ]
        nonTerms  = [s for s in clause.rhs if s.isNonterminal ]
        exact     = len([s for s in terminals  if s.modifier=="just" ])
        zeroOne   = [s for s in terminals  if s.modifier=="optional" ]
        zeroMore  = [s for s in terminals  if s.modifier=="any" ]
        oneMore   = [s for s in terminals  if s.modifier=="some" ]
        exact    += len(oneMore)
        flexible  = len(nonTerms) + len(zeroMore) + len(zeroOne) + len(oneMore)

        #print(f'count_clause: {clause.lhs} s={size} t={len(terminals)} n={len(nonTerms)}')
        if len(nonTerms)==0 and size==exact:  return 1
        if flexible==0      and size!=exact:  return 0

        freeTerms = size - exact
        if freeTerms<=0:  return 0

        combinations = 0
        for optSizes in ordered_binary_partitions_below_n(freeTerms, len(zeroOne)):
            usedTerms = sum(optSizes)
            stillFree = freeTerms - usedTerms
            for subsizes in ordered_partitions_n(stillFree, flexible):
                #print(f'  check {list(zip(nonTerms,subsizes))}')
                combinations += math.prod([ self.count_nonterminal(n, s)  for n,s in zip(nonTerms,subsizes) ])
        #print(f'  total {combinations}')

        return combinations


class Enumerator:
    def __init__(self, grammar):
        self.grammar = grammar
        self.memo    = {}

    def produce(self, ruleName, size):
        rule = self.grammar.rules[ruleName]
        for clause in rule.clauses:
            #print(f'clause: {clause}')
            for solution in self.produce_clause(clause,size):
                #print(f' {clause} -> {solution}')
                yield solution

    def produce_clause(self, clause, size):
        terminals       = [s for s in clause.rhs if s.isTerminal ]
        exact, zeroOne, zeroMore, oneMore, subTerms = [], [], [], [], []
        modifierMap = { "just":exact, "optional":zeroOne, "any":zeroMore, "some":oneMore }
        for i,s in enumerate(clause.rhs):
            if s.isTerminal:
                modifierMap[s.modifier].append((i,s))
            if s.isNonterminal:
                subTerms.append((i,s))
        def p(col):
            return ", ".join([str(c[1]) + '@' + str(c[0]) for c in col])
        #print(f'{size} of exact {p(exact)} 01 {p(zeroOne)} 0+ {p(zeroMore)} 1+ {p(oneMore)} nt {p(subTerms)}')
        freeTerms = size - len(exact) - len(oneMore)
        flexible = len(zeroMore) + len(oneMore) + len(subTerms)
        if freeTerms==0 and len(exact)+len(oneMore)>0 and \
           all([] in self.nonterm_expansion(s,0) for (_,s) in subTerms):
            result = [None] * len(clause.rhs)
            for (pos,s) in exact+oneMore:
                result[pos] = s
            for i,s in enumerate(clause.rhs):
                if not s.isTerminal and not s.isNonterminal:
                    result[i] = clause.rhs[i]
            yield [s for s in result if s is not None]
        elif freeTerms>0 and flexible>0:
            for optSizes in ordered_binary_partitions_below_n(freeTerms, len(zeroOne)):
                usedTerms = sum(optSizes)
                stillFree = freeTerms - usedTerms
                for subsizes in ordered_partitions_n(stillFree, flexible):
                    #print(f' opt: {optSizes} flex: {subsizes}')
                    result = [(),] * len(clause.rhs)
                    for i,s in enumerate(clause.rhs):
                        if not s.isTerminal and not s.isNonterminal:
                            result[i] = [clause.rhs[i]]
                    for (pos,s) in exact+oneMore:
                        result[pos] = [s]
                    for f in range(len(zeroMore)):
                        pos,symbol = zeroMore[f]
                        result[pos] = [symbol] * subsizes[f]
                    for f in range(len(zeroMore),len(zeroMore)+len(oneMore)):
                        pos,symbol = oneMore[f-len(zeroMore)]
                        result[pos] = [symbol] * (subsizes[f]+1)
                    for subSolution in self.nonterm_seq_expansion(subsizes[len(zeroMore)+len(oneMore):], subTerms):
                        for pos,terms in subSolution:
                            result[pos] = terms
                        #print(f' raw: {result}')
                        yield list(itertools.chain.from_iterable([s for s in result if len(s)>0]))

    def nonterm_seq_expansion(self, sizes, nonterms):
        #print(f' seq_exp: {strs(sizes)} {nonterms}')
        assert len(sizes)==len(nonterms), (sizes,nonterms)
        if len(sizes)==0:
            yield []
        else:
            pos,symbol = nonterms[0]
            size = sizes[0]
            for initialTerms in self.nonterm_expansion(symbol,size):
                for rest in self.nonterm_seq_expansion(sizes[1:], nonterms[1:]):
                    yield [(pos,initialTerms)] + rest

    def nonterm_expansion(self, symbol, size):
        if symbol.modifier=="just":
            for result in self.produce(symbol.name,size):
                yield result
        elif symbol.modifier=="any":
            if size==0:
                yield []
            else:
                for i in range(1,size+1):
                    for initTerms in self.produce(symbol.name,i):
                        for restTerms in self.nonterm_expansion(symbol,size-i):
                            yield initTerms + restTerms
        elif symbol.modifier=="some":
            if size>0:
                suffixSymbol = symbol.copy()
                suffixSymbol.modifier = "any"
                for i in range(1,size+1):
                    for initTerms in self.produce(symbol.name,i):
                        for restTerms in self.nonterm_expansion(suffixSymbol,size-i):
                            yield initTerms + restTerms
        elif symbol.modifier=="optional":
            if size==0:
                yield []
            for terms in self.produce(symbol.name,size):
                yield terms


def renderText(terminals):
    spacing = True
    texts   = []
    for t in terminals:
        if isinstance(t, Grammar.TermString):
            if spacing and len(texts)>0:
                texts.append(" ")
            texts.append(t.string)
        if isinstance(t, Grammar.TermSet):
            if spacing and len(texts)>0:
                texts.append(" ")
            texts.append(random.choice(list(t.chars)))
        if isinstance(t, Grammar.Glue):
            spacing = False
        if isinstance(t, Grammar.Remover):
            spacing = True
    return "".join(texts)

if __name__=='__main__':
    stage1g, _, _ = buildCommon()
    s = Sampler(stage1g)
    e = Enumerator(stage1g)
    for i in range(2,3):
        enumerated = [renderText(r) for r in e.produce('atom',i)]
        counted = s.count_rule('atom',i)
        print(f'count: {counted}  enum: {len(enumerated)}')
        print(enumerated)

