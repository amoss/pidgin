# Copyright (C) 2023 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

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


def strs(iterable):
    return " ".join([str(x) for x in iterable])


def prefixesOf(s) :
    for i in range(1,len(s)+1):
        yield s[:i]


def dump(node, depth=0):
    print(f"{'  '*depth}{type(node)}{node}")
    if hasattr(node,'children'):
        for c in node.children:
            dump(c,depth+1)


class MultiDict:
    '''This class stores a representation of graph edges as a two-level structure of keys -> value(-sets).'''
    def __init__(self):
        self.map = {}

    def store(self, k, v):
        if not k in self.map.keys():
            self.map[k] = set()
        self.map[k].add(v)
