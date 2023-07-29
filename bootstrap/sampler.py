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
        yield [min(1,total)]
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
        return sum( self.count_clause(clause,size) for clause in rule.clauses)

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

        print(f'count_clause: {clause.lhs} s={size} t={len(terminals)} n={len(nonTerms)}')
        if len(nonTerms)==0 and size==exact:  return 1
        if flexible==0      and size!=exact:  return 0

        freeTerms = size - exact
        if freeTerms<=0:  return 0

        combinations = 0
        for optSizes in ordered_binary_partitions_below_n(freeTerms, len(zeroOne)):
            usedTerms = sum(optSizes)
            stillFree = freeTerms - usedTerms
            for subsizes in ordered_partitions_n(stillFree, flexible):
                print(f'  check {list(zip(nonTerms,subsizes))}')
                combinations += math.prod([ self.count_nonterminal(n, s)  for n,s in zip(nonTerms,subsizes) ])
        print(f'  total {combinations}')

        return combinations


class Enumerator:
    def __init__(self, grammar):
        self.grammar = grammar
        self.memo    = {}

    def produce(self, ruleName, size):
        rule = self.grammar.rules[ruleName]
        for clause in rule.clauses:
            for solution in self.produce_clause(clause,size):
                yield solution

    def produce_clause(self, clause, size):
        resultAlignment = [s for s in clause.rhs      if s.isTerminal or s.isNonterminal]
        terminals       = [s for s in resultAlignment if s.isTerminal ]
        nonTerms        = [s for s in resultAlignment if s.isNonterminal ]
        exact, zeroOne, zeroMore, oneMore = [], [], [], []
        modifierMap = { "just":exact, "optional":zeroOne, "any":zeroMore, "some":oneMore }
        for i,s in enumerate(resultAlignment):
            if s.isTerminal:
                modifierMap[s.modifier].append((i,s))
        def p(col):
            return ", ".join([str(c[1]) + '@' + str(c[0]) for c in col])
        print(f'{size} of exact {p(exact)} 01 {p(zeroOne)} 0+ {p(zeroMore)} 1+ {p(oneMore)}')
        freeTerms = size - len(exact) - len(oneMore)
        flexible = len(zeroMore) + len(oneMore)
        if freeTerms == 0:
            result = [None] * len(resultAlignment)
            for (pos,s) in exact+oneMore:
                result[pos] = s
            yield [s for s in result if s is not None]
        elif freeTerms>0 and flexible>0:
            for optSizes in ordered_binary_partitions_below_n(freeTerms, len(zeroOne)):
                usedTerms = sum(optSizes)
                stillFree = freeTerms - usedTerms
                for subsizes in ordered_partitions_n(stillFree, flexible):
                    print(f'opt: {optSizes} flex: {subsizes}')
                    result = [(),] * len(resultAlignment)
                    for (pos,s) in exact+oneMore:
                        result[pos] = [s]
                    for f in range(len(zeroMore)):
                        pos,symbol = zeroMore[f]
                        result[pos] = [symbol] * subsizes[f]
                    yield list(itertools.chain.from_iterable([s for s in result if len(s)>0]))






if __name__=='__main__':
    stage1g, _, _ = buildCommon()
    #s = Sampler(stage1g)
    e = Enumerator(stage1g)
    for i in range(0,5):
        for r in e.produce('str_lit2',i):
            print(f'Solution: {strs(r)}')

