# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os, sys
rootDir= os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

import math
import random
from bootstrap.grammar import Grammar
from bootstrap.interpreter import buildCommon, stage2


def ordered_partitions_n(total, length):
    if length==0:
        yield []
    if length==1:
        yield [total]
    else:
        for i in range(total+1):
            for suffix in ordered_partitions_n(total-i,length-1):
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

    def count_clause(self, clause, size):
        terminals = [s for s in clause.rhs if s.isTerminal ]
        nonTerms  = [s for s in clause.rhs if s.isNonterminal ]
        print(f'count_clause: {clause.lhs} s={size} t={len(terminals)} n={len(nonTerms)}')
        if len(nonTerms)==0 and size==len(terminals):  return 1
        if len(nonTerms)==0 and size!=len(terminals):  return 0

        freeTerms = size - len(terminals)
        if freeTerms<=0:  return 0

        combinations = 0
        for subsizes in ordered_partitions_n(freeTerms, len(nonTerms)):
            print(f'  check {list(zip(nonTerms,subsizes))}')
            combinations += math.prod([ self.count_rule(n.name, s)  for n,s in zip(nonTerms,subsizes) ])
        print(f'  total {combinations}')

        return combinations

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

if __name__=='__main__':
    stage1g, _, _ = buildCommon()
    s = Sampler(stage1g)
    for i in range(1,5):
        print(s.count_rule('ident',i))

