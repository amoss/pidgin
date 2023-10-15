# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

import argparse
import itertools
import math
import operator
import random
import string
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


class ClauseAllocation:
    '''In sampling, enumeration and counting we face a common sub-problem. Given a clause (i.e. the r.h.s. of
       a production) as a sentential form we have terminals in the forms: T, T?, T*, T+ and non-terminals with
       the same possible modifiers. If we know the total number of terminals in the final productions we must
       decide how to partition them over the symbols in the clause in a way that respects the modifiers.

       The *assignments* method generates the lists of terminal-sizes assigned to each part of the clause. The
       caller must ensure that the assignment to each non-terminal is valid (i.e. there may not exist an
       expansion of that non-terminal to the number of terminals). The assignments to each kind of
       terminal-modifier are valid as the sizes of each kind of expansion is dense, i.e. 1, 0-1, 0+, 1+.
    '''
    def __init__(self, clause):
        self.one       = []
        self.zeroOne   = []
        self.zeroMore  = []
        self.oneMore   = []
        self.nonterms  = []
        self.zero      = []
        modifierMap = { "just":self.one, "optional":self.zeroOne, "any":self.zeroMore, "some":self.oneMore }
        for i,symbol in enumerate(clause):
            if symbol.isTerminal:
                modifierMap[symbol.modifier].append( (i,symbol) )
            elif symbol.isNonterminal:
                self.nonterms.append( (i,symbol) )
            else:
                self.zero.append( (i,symbol) )
        self.numFlexible = len(self.zeroMore) + len(self.oneMore) + len(self.nonterms)
        self.posNonterms = len(self.zeroOne) + len(self.zeroMore) + len(self.oneMore)
        self.posOneMore  = len(self.zeroOne) + len(self.zeroMore)
        self.assignmentOrder = self.zeroOne + self.zeroMore + self.oneMore + self.nonterms
        self.offset      = [ 1 if i>=self.posOneMore and i<self.posNonterms else 0
                             for i in range(len(self.assignmentOrder)) ]

    def assignments(self, size):
        freeTerms = size - len(self.one) - len(self.oneMore)
        if freeTerms==0:
            #yield [0] * (len(self.zeroOne) + self.numFlexible)
            yield self.offset   # 1 for each oneMore and 0 elsewhere
        elif freeTerms>0  and  len(self.zeroMore)+self.numFlexible>0:
            for optSizes in ordered_binary_partitions_below_n(freeTerms, len(self.zeroOne)):
                stillFree = freeTerms - sum(optSizes)
                for subsizes in ordered_partitions_n(stillFree, self.numFlexible):
                    yield list(map(operator.add, optSizes+subsizes, self.offset))  # insert +1 to oneMore counts

    def assignment_nonterms(self, assignment):
        for i in range(len(self.nonterms)):
            yield (assignment[self.posNonterms+i], self.nonterms[i][1])

def weighted_choice(keys_weights):
    if len(keys_weights)==1:   return keys_weights[0][0]
    total = sum(w for _,w in keys_weights)
    assert total>0, keys_weights
    choice = random.randrange(total)
    weight_sum = 0
    for pos,(key,weight) in enumerate(keys_weights):
        if choice < weight_sum+weight:
            return key
        weight_sum += weight
    assert False

class Sampler:
    def __init__(self, grammar):
        self.grammar = grammar
        self.memo    = {}

    def sample_rule(self, ruleName, size, bias=[]):
        rule = self.grammar.rules[ruleName]
        choices = [ (clause, self.count_clause(clause,size,bias))  for clause in rule.clauses ]
        for clause,count in choices:
            print(clause,count)
        if sum(count for _,count in choices)==0:
            return None
        clause = weighted_choice(choices)
        return self.sample_clause(clause, size, bias)

    def count_rule(self, ruleName, size, bias, dbgdepth=''):
        key = (ruleName,size)
        if key in self.memo:
            return self.memo[key]
        rule = self.grammar.rules[ruleName]
        result = sum( self.count_clause(clause,size,bias, dbgdepth=dbgdepth+'  ') for clause in rule.clauses)
        self.memo[key] = result
        return result

    def count_nonterminal(self, symbol, size, bias, dbgdepth=''):
        print(f'{dbgdepth}count_nonterminal {symbol} {size} {bias}')
        biasCount = None
        for name,count in bias:
            if name==symbol.name:
                biasCount = count
        print(f'{dbgdepth} biasCount={biasCount}')
        if biasCount==0:
            return 0
        key = (symbol,size,tuple(bias))
        if key in self.memo:
            print(f'{dbgdepth} memo {key} <- {self.memo[key]}')
            return self.memo[key]
        if symbol.modifier=="just":
            if biasCount is None:
                result = self.count_rule(symbol.name, size, bias, dbgdepth=dbgdepth+'  ')
            else:
                newBias = [(name,count) if name!=symbol.name else (name,biasCount-1) for name,count in bias]
                print(f'{dbgdepth}bias {biasCount} for {symbol} -> {newBias} ({size})')
                result = self.count_rule(symbol.name, size, newBias, dbgdepth=dbgdepth+'  ')
            self.memo[key] = result
            print(f'{dbgdepth} set memo = {result} {symbol}@{size}')
            return result
        if symbol.modifier=="any":
            if size==0:  return 1
            combinations = 0
            # Blow up as termsize * biasNum
            for prefix in range(1,size+1):
                combinations += self.count_rule(symbol.name, prefix, bias, dbgdepth=dbgdepth+'  ') * \
                                self.count_nonterminal(symbol, size-prefix, bias, dbgdepth=dbgdepth+'  ')
            self.memo[key] = combinations
            print(f'{dbgdepth} set memo = {combinations} {symbol}@{size}')
            return combinations
        if symbol.modifier=="some":
            if size==0:  return 0
            combinations = 0
            suffixSymbol = symbol.copy()
            suffixSymbol.modifier = "any"
            # Blow up as termsize * biasNum
            for prefix in range(1,size+1):
                combinations += self.count_rule(symbol.name, prefix, bias, dbgdepth=dbgdepth+'  ') * \
                                self.count_nonterminal(suffixSymbol, size-prefix, bias, dbgdepth=dbgdepth+'  ')
            self.memo[key] = combinations
            print(f'{dbgdepth} set memo = {combinations} {symbol}@{size}')
            return combinations
        if symbol.modifier=="optional":
            if size==0:  return 1
            result = self.count_rule(symbol.name, size, bias, dbgdepth=dbgdepth+'  ')
            self.memo[key] = result
            print(f'{dbgdepth} set memo = {result} {symbol}@{size}')
            return result
        assert False


    def sample_clause(self, clause, size, bias):
        alloc = ClauseAllocation(clause.rhs)
        choices = [ (counts, math.prod(self.count_nonterminal(nonterm, subsize, bias)
                                      for subsize,nonterm in alloc.assignment_nonterms(counts)))
                    for counts in alloc.assignments(size) ]
        choices = [ c for c in choices if c[1]>0 ]
        if len(choices)==0:
            counts = []
        else:
            counts = weighted_choice(choices)
        result = [(),] * len(clause.rhs)
        for pos,symbol in alloc.zero+alloc.one:
            result[pos] = [symbol]
        combined = list(zip(counts, alloc.assignmentOrder))
        for count,(pos,symbol) in combined[:alloc.posNonterms]:
            result[pos] = [symbol]*count
        for count,(pos,symbol) in combined[alloc.posNonterms:]:
            if count>0:
                result[pos] = self.sample_rule(symbol.name,count)
        return list(itertools.chain.from_iterable([s for s in result if len(s)>0]))


    def count_clause(self, clause, size, bias, dbgdepth=''):
        print(f'{dbgdepth}count_clause {clause} {size} {bias}')
        key = (clause,size,tuple(bias))
        if key in self.memo:
            return self.memo[key]
        alloc = ClauseAllocation(clause.rhs)
        combinations = 0
        for counts in alloc.assignments(size):
            print(f'{dbgdepth} counts={counts} bias={bias}')
            # If we have bias parameters then we cannot avoid the combinatorial blowup of applying the counting
            # function while checking the distribution (via partition of the integer) of each of number of
            # the biased non-terminal to each sub-clause (non-terminal expansion) in the clause.
            if len(bias)>0:
                all_nonterms = [ (numTerms,symbol) for numTerms,symbol in alloc.assignment_nonterms(counts)]
                nonterms = [ (numTerms,symbol) for numTerms,symbol in all_nonterms if numTerms>0 ]
                #print(f' nonterms={nonterms}')
                # If we have no nonterminal sub-productions to distribute the bias onto then there
                # are 0 valid expansions matching the bias.
                if len(nonterms)>0:
                    biasNames, biasCounts = zip(*bias)
                    biasDists = [ ordered_partitions_n(count, len(nonterms)) for count in biasCounts ]
                    biasAssignments = list(itertools.product(*biasDists))
                    #print(f' biasAssignments={biasAssignments}')
                    for assignment in biasAssignments:
                        subBias = list(zip(biasNames,assignment))
                        assignedCombinations = [ self.count_nonterminal(nonterm, subsize,
                                                                         [(sb[0],sb[1][i]) for sb in subBias], dbgdepth=dbgdepth+'  ')
                                                 for i,(subsize,nonterm) in enumerate(nonterms) ]
                        #print(f' {assignment} -> {assignedCombinations}')
                        combinations += math.prod(assignedCombinations)
                else:
                    if all(self.count_nonterminal(nt,0,bias,dbgdepth)>0 for _,nt in all_nonterms):   
                        print(f'{dbgdepth} ADDONE from {all_nonterms}')
                        # TODO: We still need to check that it is valid to count the nonterms at size zero......
                        if sum(v for _,v in bias)==0:
                            combinations += 1
                    else:
                        print(f'SKIP ADDONE from {all_nonterms}')
            else:
                combinations += math.prod(self.count_nonterminal(nonterm, subsize, bias, dbgdepth=dbgdepth+'  ')
                                          for subsize,nonterm in alloc.assignment_nonterms(counts))
        self.memo[key] = combinations
        print(f'{dbgdepth}combinations={combinations} {size}@{clause}')
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
        alloc = ClauseAllocation(clause.rhs)

        for counts in alloc.assignments(size):
            result = [(),] * len(clause.rhs)
            for pos,symbol in alloc.zero+alloc.one:
                result[pos] = [symbol]
            combined = zip(counts, alloc.assignmentOrder)
            for count,(pos,symbol) in combined:
                result[pos] = [symbol]*count
            for subSolution in self.nonterm_seq_expansion(counts[alloc.posNonterms:],
                                                          alloc.assignmentOrder[alloc.posNonterms:]):
                for pos,terms in subSolution:
                    result[pos] = terms
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
            if t.inverse:
                universe = set(string.printable).difference(t.chars)
                texts.append(random.choice(list(universe)))
            else:
                texts.append(random.choice(list(t.chars)))
        if isinstance(t, Grammar.Glue):
            spacing = False
        if isinstance(t, Grammar.Remover):
            spacing = True
    return "".join(texts)

if __name__=='__main__':
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-g", "--grammar", type=str, default="bootstrap/interpreter/grammar.g")
    argParser.add_argument("-s", "--size", type=int, default=10)
    argParser.add_argument("-r", "--rule", type=str, default="program")
    argParser.add_argument("-b", "--bias", action='append')
    argParser.add_argument("-n", "--numresults", type=int, default=20)
    args = argParser.parse_args()
    bias = [] if args.bias is None else [ s.split('=') for s in args.bias ]
    bias = [ (name,int(count)) for name,count in bias ]
    stage1g, _, stage1 = buildCommon()
    res = next(stage1.execute( open(args.grammar).read()), None)
    if res is None:
        print(f"Failed to parse grammar from {args.grammar}")
        sys.exit(-1)
    grammar = stage2(res)
    s = Sampler(grammar)
    for i in range(args.numresults):
        print(renderText(s.sample_rule(args.rule,args.size,bias=bias)))

