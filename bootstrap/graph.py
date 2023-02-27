# Copyright (C) 2003 Dr Andrew Moss.    You should have received a copy of the GNU General Public License
#                                       along with this program.  If not, see <https://www.gnu.org/licenses/>.

def partition(predicate, iterable):
    inside, outside = [], []
    for x in iterable:
        if predicate(x):
            inside.append(x)
        else:
            outside.append(x)
    return inside, outside


class Graph:
    class Node:
        def __init__(self, label):
            if isinstance(label,set) or isinstance(label,frozenset):
                self.labels = label
            else:
                self.labels = set([label])

    class Edge:
        def __init__(self, source, target, label):
            self.source = source
            self.target = target
            self.label  = label
        def __hash__(self):
            return hash( (self.source, self.target, self.label) )
        def __eq__(self, other):
            return  self.source==other.source and self.target==other.target and self.label==other.label

    def __init__(self):
        self.nodes = set()
        self.nodeLabels = {}
        self.edges = set()
        self.start = None

    def findEdgeBySource(self, source):
        for e in self.edges:
            if e.source==source:
                yield e

    def findEdgeByTarget(self, target):
        for e in self.edges:
            if e.target==target:
                yield e

    def findEdgeByLabel(self, label):
        for e in self.edges:
            if e.label==label:
                yield e

    def force(self, label):
        '''Retrieve the node with the label if one exists otherwise create a node for the label.'''
        if isinstance(label,set):
            for l in label:
                if l in self.nodeLabels:
                    return self.nodeLabels[l]
            result = Graph.Node(label)
            self.nodes.add( result)
            for l in label:
                self.nodeLabels[l] = result
            return result
        else:
            if label in self.nodeLabels:
                return self.nodeLabels[label]
            result = Graph.Node(label)
            self.nodes.add( result )
            self.nodeLabels[label] = result
            return result

    def remove(self, node):
        #print(f"Removing {node}")
        self.edges = self.edges.difference(self.findEdgeBySource(node))
        self.edges = self.edges.difference(self.findEdgeByTarget(node))
        self.nodes = self.nodes.difference([node])
        self.nodeLabels = {k:v for k,v in self.nodeLabels.items() if v!=node}

    def connect(self, source, target, label):
        assert isinstance(source,Graph.Node) and source in self.nodes, str(source)
        assert target is None or (isinstance(target,Graph.Node) and target in self.nodes), str(target)
        self.edges.add( Graph.Edge(source,target,label) )

    def fold(self, edge):
        #print(f"Folding {id(edge.source)} {id(edge.target)} {edge.label}")
        source = edge.source
        target = edge.target
        if source==target:
            self.edges.remove(edge)
            return

        outgoing  = set( [ (e.target, e.label) for e in self.findEdgeBySource(source) ] +
                         [ (e.target, e.label) for e in self.findEdgeBySource(target) ] )
        selfLoopsOut, outgoing = partition(lambda x:(x[0]==source or x[0]==target), outgoing)
        #print(f"Outgoing: {outgoing} {selfLoopsOut}")

        incoming  = set( [ (e.source, e.label) for e in self.findEdgeByTarget(source) ] +
                         [ (e.source, e.label) for e in self.findEdgeByTarget(target) ] )
        selfLoopsIn, incoming = partition(lambda x:(x[0]==source or x[0]==target), incoming)

        selfLoops = set( map(lambda x:x[1], selfLoopsOut)).union( map(lambda x:x[1], selfLoopsIn))
        selfLoops.difference(edge.label)

        self.remove(source)
        self.remove(target)
        srcLabel = source.labels if isinstance(source.labels, set) else set([source.labels])
        tarLabel = target.labels if isinstance(target.labels, set) else set([target.labels])
        merged = self.force(srcLabel.union(tarLabel))
        if self.start in (source,target):
            self.start = merged
        for (target,label) in outgoing:
            self.connect(merged, target, label)
        for (source,label) in incoming:
            self.connect(source, merged, label)
        for label in selfLoops:
            self.connect(merged, merged, label)

    def dot(self, output):
        print("digraph {", file=output)
        for n in self.nodes:
            label = "\\n".join([str(l) for l in n.labels])
            print(f'n{id(n)} [label="{label}"];', file=output)
        for e in self.edges:
            if e.target is not None:
                print(f'n{id(e.source)} -> n{id(e.target)} [label="{e.label}"];', file=output)
            else:
                print(f'n{id(e.source)} [shape=rect];', file=output)
        print("}", file=output)

    def dump(self):
        for e in self.edges:
            print(e)

