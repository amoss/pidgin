import functools
import itertools
import operator
from graph import Graph
from grammar import Grammar

g = Grammar("lst")
g.addRule("expr", [g.Terminal("("), g.Nonterminal("expr","any"), g.Terminal(")")])
g.addRule("lst",  [g.Nonterminal("expr","some")])

def strs(iterable):
    return " ".join([str(x) for x in iterable])

class Generator:
    def __init__(self, grammar):
        self.grammar   = grammar
        self.templates = set()
        self.forms     = set([self.Form(grammar, [grammar.Nonterminal(grammar.start,"just")])])
        self.done      = set()

    def step(self):
        while True:
            #print(f"\nStep: templates={strs(self.templates)}")
            #print(f"      forms={strs(self.forms)}")
            next = set()
            for t in self.templates:
                #print(f"Generating from template {t}")
                newForm = self.Form(self.grammar, t.next())
                if not newForm in self.done:
                    self.forms.add(newForm)
            for form in self.forms:
                #print(f"Considering {f}")
                for sub in form.substitutions():
                    self.done.add(form)
                    if Generator.isTemplate(sub):
                        #print(f"  new Gen: {strs(sub)}")
                        self.templates.add(self.Template(self.grammar,sub))
                    elif Generator.isAllTerminal(sub):
                        yield sub
                        #print(f"  Emit: {strs(sub)}")
                    else:
                        #print(f"  new Form: {strs(sub)}")
                        newForm = self.Form(self.grammar,sub)
                        if not newForm in self.done:
                            next.add(newForm)
            self.forms = next

    @staticmethod
    def isTemplate(symbols):
        return any([s.modifier in ("any","some") for s in symbols])

    @staticmethod
    def isAllTerminal(symbols):
        return all([s.isTerminal() for s in symbols])

    @staticmethod
    def tuples(size, total):
        '''Enumerate all integer-tuples of *size* with elements that sum to *total*.'''
        yield (0,) * (size-1) + (total,)
        for sig in range(1,size):               # position of leading-non-zero, indexed from end
            prefix = (0,) * (size-sig-1)
            for dig in range(1,total+1):
                for suffix in Generator.tuples(sig, total-dig):
                    yield prefix + (dig,) + suffix

    #    class Counter:
    #        '''Sentences in the generator contain symbols that can be repeated an arbitrary number of times. This
    #           class models a fair counter over the tuple of repetition counts. It will enumerate all valid counts
    #           of repetition giving each individual count the same rate of progress. If we consider the tuple to be
    #           a number in an arbitrarily high base, then each count is a digit. If we simply increment the counter
    #           then the final digit will increase forever and no other digit will change.
    #
    #           Fairness in the counter means that increases in digits will be evenly distributed across all digit
    #           positions. The trick is the same enumeration order use to prove that tuples are countable, i.e. for
    #           n-dimensions a series of (n-1)-dimensional planes at 45 degrees to the axis that cover the space.
    #
    #           This is equivalent to enumerating all tuples with the same total, so that the totals are the sequence
    #           of integers, i.e. permuations of partitions of the integers with a length up to the length of the
    #           tuple.
    #        '''


    class Template:
        '''A sentential form (sequence of *symbols* derived from the grammar) with at least one repeating modifier
           (any or some). This can be used to generate an infinite family of sentential forms with a common shape.
           The *Template* is stateful (remembering the counts of each repeating symbol) but the comparison is done
           over the stateless definition (just the sentential form).'''
        def __init__(self, grammar, symbols):
            self.grammar   = grammar
            self.symbols   = tuple(symbols)
            self.positions = ()
            self.offset    = ()

            for i,s in enumerate(symbols):
                if s.modifier=="any":
                    self.positions += (i,)
                    self.offset    += (0,)
                if s.modifier=="some":
                    self.positions += (i,)
                    self.offset    += (1,)

            self.total     = 0
            self.tuples    = Generator.tuples(len(self.positions), self.total)
            self.nextTuple = next(self.tuples)

        def __str__(self):
            return f"Template({strs(self.symbols)}@{self.nextTuple})"

        def __eq__(self, other):
            return isinstance(other,Template) and self.symbols==other.symbols

        def __hash__(self):
            return hash(self.symbols)

        def next(self):
            result = self.instantiate(tuple(h+o for h,o in zip(self.nextTuple,self.offset)))
            try:
                self.nextTuple = next(self.tuples)
            except StopIteration:
                self.total += 1
                self.tuples    = Generator.tuples(len(self.positions), self.total)
                self.nextTuple = next(self.tuples)
            return result

        def instantiate(self, counts):
            result = []
            position = 0
            for s in self.symbols:
                if s.modifier in ("any","some"):
                    result.extend([s.exactlyOne()] * counts[position])
                    position += 1
                else:
                    result.append(s)
            return result


    class Form:
        '''A sentential form (sequence of *symbols* derived from the grammar) without any repeating modifiers (only
           optional or just). This can be used to generate a finite family of forms/sentences by substitution of
           non-terminals.'''
        def __init__(self, grammar, symbols):
            self.grammar = grammar
            self.symbols = tuple(symbols)
            for s in symbols:
                assert s.modifier in ('just', 'optional'), s.modifier

        def __str__(self):
            return f"Form({strs(self.symbols)})"

        def substitutions(self):
            variations = []
            for s in self.symbols:
                if s.isTerminal():
                    if s.modifier=="optional":
                        variations.append([[], [s.exactlyOne()]])
                    else:
                        variations.append([[s]])
                else:
                    variations.append([list(clause.rhs) for clause in self.grammar.rules[s.name].clauses])

            cart_product = itertools.product(*variations)
            for sentenceParts in cart_product:
                sentence = functools.reduce(operator.iconcat, sentenceParts, [])
                yield sentence

        def __eq__(self, other):
            return isinstance(other,Form) and self.symbols==other.symbols

        def __hash__(self):
            return hash(self.symbols)




generator = Generator(g)
sentences = list(itertools.islice(generator.step(), 20))
for s in sentences:
    s = [ symb.string if symb.string is not None else symb for symb in s]
    print(f"Emit {strs(s)}")

#// 0 1 2 3 4 5
#// 0,0  0,1  1,0  0,2  1,1  2,0  3,0  2,1  1,2 0,3 ...
#// 0,0,0  0,0,1  0,1,0  1,0,0  0,0,2  0,1,1  1,0,1  0,2,0  1,1,0
#// 0,0,0,0  0,0,0,1  0,0,1,0  0,1,0,0  1,0,0,0  0,0,0,2  0,0,1,1 0,1,0,1  0,1,1,0  

#// The zig-zagging structure is used as an argument that all countable infinities have a bijective mapping
#// We can view it enumerating n-1 dimenional planes at 45 degrees through the space
#// It is equivalent to permutations of the partitions of the integers
#// It is equivalent to a counting system stratified by the sum of the digits

