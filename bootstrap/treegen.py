import random

class Node:
    def __init__(self, children=None):
        if children is None:
            self.children = []
        else:
            self.children = children

    def __str__(self):
        return 'n(' + ",".join([str(c) for c in self.children]) + ')'

    def depth(self):
        result = 0
        for c in self.children:
            result = max(result, c.depth()+1)
        return result

    def size(self):
        result = 1
        for c in self.children:
            result += c.size()
        return result

    def add(self):
        self.children.append(Node())
        return self.children[-1]

class Distribution:
    def __init__(self):
        self.store = {}

    def add(self, item):
        key = str(item)
        if not key in self.store:
            self.store[key] = 1
        else:
            self.store[key] = self.store[key]+1

    def dump(self):
        for k in sorted(self.store.keys()):
            print(f'{k} : {self.store[k]}')

    def maxRatio(self):
        high = max(self.store.values())
        low  = min(self.store.values())
        return high/low


# Different approaches for generating random trees:
#  1. Pick a random node, add a child
#       Results show this is very skewed and non-uniform. I wonder if this is equivalent to a Prufer sequence
#       but without the normalization step from picking the degrees first and then joining?
#  2. Generate a Prufer sequence, convert to tree
#  3. Partition the number of remaining nodes and generate subtrees
#  4. Start with forest of nodes, choose joins.
#  5. Random walk down tree, deciding where to add node


def ip(n,k=None):
    if n==0:                          return [[]]
    if n==1:                          return [[1]]
    if k is None:                     k=n
    ip.memo = getattr(ip,'memo',{})
    if (n,k) in ip.memo:              return ip.memo[(n,k)]

    result = []
    for i in range(min(k,n),0,-1):
        for suffix in ip(n-i, min(k,i)):
            result.append([i] + suffix)
    ip.memo[(n,k)] = result
    return result


def count_partitions(n,max_int=None):
    count_partitions.memo = getattr(count_partitions,'memo',{})
    if n==0:                                     return 1
    if n==1:                                     return 1
    if max_int is None:                          max_int=n
    if (n,max_int) in count_partitions.memo:     return count_partitions.memo[(n,max_int)]

    count = 0
    for i in range(min(max_int,n),0,-1):         count += count_partitions(n-i, min(max_int,i))
    count_partitions.memo[(n,max_int)] = count
    return count



def child_degrees(max_nodes, length, max_degree):
    if max_nodes==0:
        yield [0] * length
    elif length==1:
        yield [min(max_nodes,max_degree)]
    else:
        for i in range(min(max_nodes,max_degree)+1):
            for suffix in child_degrees(max_nodes-i,length-1,max_degree):
                yield [i] + suffix


def trees_from_spec(max_degree, spec):
    if len(spec)==0:
        yield []
    else:
        for tree in trees(max_degree, spec[0][0], spec[0][1]):
            for suffix in trees_from_spec(max_degree, spec[1:]):
                yield [tree] + suffix

def trees(max_degree, root_degree, nodes):
    if nodes==0:
        yield Node()
    else:
        for spec in tree_child_specs(max_degree, root_degree, nodes):
            for children in trees_from_spec(max_degree, spec):
                yield Node(children=children)


def tree_child_specs(max_degree, root_degree, nodes):
    assert nodes >= root_degree
    free_nodes = nodes - root_degree
    if root_degree==1:
        if nodes-1 == 0:
            yield [(0,0)]
        else:
            for degree in range(1,min(nodes-1,max_degree)+1):
                yield [(degree,nodes-1)]
    else:
        for suffix in tree_child_specs(max_degree, root_degree-1, nodes-1):
            yield [(0,0)] + suffix
        for left_size in range(1,free_nodes+1):
            for left_degree in range(1, min(max_degree,left_size)+1):
                for suffix in tree_child_specs(max_degree, root_degree-1, nodes-left_size-1):
                    yield [(left_degree,left_size)] + suffix
        




