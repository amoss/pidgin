import math, random

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
        print(f'Max ratio: {self.maxRatio()}')

    def maxRatio(self):
        high = max(self.store.values())
        low  = min(self.store.values())
        return high/low


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


# Rough sketch

def child_degrees(max_nodes, length, max_degree):
    if max_nodes==0:
        yield [0] * length
    elif length==1:
        yield [min(max_nodes,max_degree)]
    else:
        for i in range(min(max_nodes,max_degree)+1):
            for suffix in child_degrees(max_nodes-i,length-1,max_degree):
                yield [i] + suffix

# Specification generator for subtrees (auxillery)

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

# Tree generator (wrt spec generator auxillery)

def trees_from_spec(max_degree, spec):
    if len(spec)==0:
        yield []
    else:
        for tree in trees_of_degree(max_degree, spec[0][0], spec[0][1]):
            for suffix in trees_from_spec(max_degree, spec[1:]):
                yield [tree] + suffix


def trees_of_degree(max_degree, root_degree, nodes):
    if nodes==0:
        yield Node()
    else:
        for spec in tree_child_specs(max_degree, root_degree, nodes):
            for children in trees_from_spec(max_degree, spec):
                yield Node(children=children)

def trees(max_degree, nodes):
    if nodes==0:
        yield Node()
    else:
        for degree in range(1,min(nodes,max_degree)+1):
            for tree in trees_of_degree(max_degree, degree, nodes):
                yield tree

# Tree counting function (wrt spec generator auxillery)

def count_by_degree(max_degree, root_degree, nodes):
    if nodes==0:
        return 1
    combinations = [ count_by_spec(max_degree,spec) for spec in tree_child_specs(max_degree, root_degree, nodes) ]
    return sum(combinations)

def count_by_spec(max_degree, spec):
    return math.prod(count_by_degree(max_degree, degree, size) for (degree,size) in spec)

def count_tree(max_degree, nodes):
    if nodes==0:
        return 1
    return sum(count_by_degree(max_degree, degree, nodes) for degree in range(1,min(nodes,max_degree)+1) )

# Memoised counting function

def memo_count(max_degree, root_degree, nodes):
    '''Note that this functions counts both the number of trees with *nodes* below the root arranged so that
       there are *root_degree* immediate children, and the number of forests with *root_degree* trees containing
       a total of *nodes*. These are the same because we use the count of nodes within the tree (i.e. not
       counting the root). In particular the product in the innermost loop is used the number of trees on the
       left and the number of forests on the right.'''
    memo_count.table = getattr(memo_count,'table',{})
    key = (max_degree,root_degree,nodes)
    if key in memo_count.table:      return memo_count.table[key]
    if root_degree==1:
        if nodes-1==0:
            return 1
        subtrees = sum(memo_count(max_degree,degree,nodes-1) for degree in range(1,min(nodes-1,max_degree)+1))
        memo_count.table[key] = subtrees
        return subtrees
    combinations = memo_count(max_degree, root_degree-1, nodes-1)   # First child leaf combinations
    free_nodes = nodes - root_degree
    for left_size in range(1,free_nodes+1):
        for left_degree in range(1, min(max_degree,left_size)+1):
            combinations += memo_count(max_degree, left_degree, left_size) * \
                            memo_count(max_degree, root_degree-1, nodes-left_size-1)
    memo_count.table[key] = combinations
    return combinations

def memo_tree(max_degree, nodes):
    if nodes==0:
        return 1
    return sum(memo_count(max_degree, degree, nodes) for degree in range(1,min(nodes,max_degree)+1) )

# Tree sampler

def weighted_choice(keys_weights):
    if len(keys_weights)==1:   return keys_weights[0][0]
    #print(keys_weights)
    total = sum(w for _,w in keys_weights)
    choice = random.randrange(total)
    weight_sum = 0
    for pos,(key,weight) in enumerate(keys_weights):
        #print(f'key:{key}   weight: {weight}')
        if choice < weight_sum+weight:
            return key
        weight_sum += weight
    assert False

def tree_sample_by_degree(max_degree, root_degree, nodes):
    assert (nodes>0) == (root_degree>0)
    if nodes==0:         return Node()
    if root_degree==1:   return Node([tree_sample(max_degree, nodes-1)])
    #print(f'sample degree={root_degree} node={nodes}')
    free_nodes = nodes - root_degree
    if free_nodes==0:    return Node([Node() for i in range(root_degree)])
    combs_by_spec = [ ((0,0), memo_count(max_degree, root_degree-1, nodes-1)) ] \
                  + [ ((left_size,left_degree),memo_count(max_degree, left_degree, left_size) *
                                               memo_count(max_degree, root_degree-1, nodes-left_size-1))
                         for left_size in range(1,free_nodes+1)
                         for left_degree in range(1, min(max_degree,left_size)+1)
                     ]
    left_size, left_degree = weighted_choice(combs_by_spec)

    first_child = tree_sample_by_degree(max_degree, left_degree, left_size)
    rest        = tree_sample_by_degree(max_degree, root_degree-1, nodes-left_size-1)
    children    = [first_child] + rest.children
    return Node(children)


def tree_sample(max_degree, nodes):
    if nodes==0: return Node()
    combs_by_degree = [ (degree,memo_count(max_degree,degree,nodes)) for degree in range(1,min(max_degree,nodes)+1) ]
    degree = weighted_choice(combs_by_degree)
    return tree_sample_by_degree(max_degree, degree, nodes)


d = Distribution()
n = 5
for i in range(100000):
    #d.add( random.randrange(50) )
    d.add( tree_sample(3,n) )
d.dump()







