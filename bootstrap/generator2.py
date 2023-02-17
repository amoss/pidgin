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

    def step(self, trace=None):
        if trace:
            print("digraph {", file=trace)
            if trace: self.dotForm(trace, list(self.forms)[0])
            counter = 0
        while True:
            next = set()
            for t in self.templates:
                usedTuple = t.nextTuple
                newForm = self.Form(self.grammar, t.next())
                if not newForm in self.done:
                    if trace:
                        self.dotForm(trace,newForm)
                        print(f't{id(t)} -> f{id(newForm)} [label="{usedTuple}"];', file=trace)
                    self.forms.add(newForm)
            for form in self.forms:
                for sub in form.substitutions():
                    self.done.add(form)
                    if Generator.isTemplate(sub):
                        newTemplate = self.Template(self.grammar,sub)
                        self.templates.add(newTemplate)
                        if trace:
                            print(f'f{id(form)} -> t{id(newTemplate)};', file=trace)
                            self.dotTemplate(trace,newTemplate)
                    elif Generator.isAllTerminal(sub):
                        yield sub
                        if trace:
                            print(f'e{counter} [shape=rect,color=red,label="{self.dotSentence(sub)}"];', file=trace)
                            print(f'f{id(form)} -> e{counter};', file=trace)
                            counter += 1
                    else:
                        newForm = self.Form(self.grammar,sub)
                        if not newForm in self.done:
                            next.add(newForm)
                            if trace:
                                self.dotForm(trace,newForm)
                                print(f'f{id(form)} -> f{id(newForm)};', file=trace)
            self.forms = next

    @staticmethod
    def isTemplate(symbols):
        return any([s.modifier in ("any","some") for s in symbols])

    @staticmethod
    def isAllTerminal(symbols):
        return all([s.isTerminal() for s in symbols])

    @staticmethod
    def dotTemplate(output, gen):
        print(f't{id(gen)} [shape=rect,color=blue,label="{Generator.dotSentence(gen.symbols)}"];', file=output)


    @staticmethod
    def dotSentence(sentence):
        label = ''
        for i,symbol in enumerate(sentence):
            if i!=0:
                label += ' '
            if isinstance(symbol,Grammar.Terminal) and symbol.string is not None:
                label += symbol.string
            if isinstance(symbol,Grammar.Terminal) and symbol.string is None:
                label += '[' + symbol.chars + ']'
            if isinstance(symbol,Grammar.Nonterminal):
                label += symbol.name
            if symbol.modifier=="any":
                label += '*'
            if symbol.modifier=="some":
                label += '+'
            if symbol.modifier=="optional":
                label += '?'
        return label

    @staticmethod
    def dotForm(output, form):
        print(f'f{id(form)} [shape=none,color=black,label="{Generator.dotSentence(form.symbols)}"];', file=output)

    @staticmethod
    def tuples(size, total):
        '''Enumerate all integer-tuples of *size* with elements that sum to *total*. The implementation is a
           recursive generator as it give a clean expression of the function, although it is equivalent to taking
           the partitions of the integer *total, filtering them to keep those with a length of *size* and then
           enumerating the permutations.'''
        yield (0,) * (size-1) + (total,)
        for sig in range(1,size):               # position of leading-non-zero, indexed from end
            prefix = (0,) * (size-sig-1)
            for dig in range(1,total+1):
                for suffix in Generator.tuples(sig, total-dig):
                    yield prefix + (dig,) + suffix

    class Template:
        '''A sentential form (sequence of *symbols* derived from the grammar) with at least one repeating modifier
           (any or some). This can be used to generate an infinite family of sentential forms with a common shape.
           The *Template* is stateful (remembering the counts of each repeating symbol) but the comparison is done
           over the stateless definition (just the sentential form).

           The enumeration of the counts is fair - rather than increment one count indefinitely and "starve" the
           other counts of increments. The trick here is the same as proving that tuples are in a bijection with
           the integers by "zig zagging" through the space rather than iterating parallel to an axis. We iterate
           over all tuples with the same sum, and then increase the sum.'''
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
traceFile = open('trace.dot','wt')
sentences = list(itertools.islice(generator.step(trace=traceFile), 20))
print("}", file=traceFile)
traceFile.close()
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

