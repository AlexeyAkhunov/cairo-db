# Operations with WBT trees


# generates initial set of composite keys and correcsponding values pseudorandomly, given initial setting
# it writes the initial set into a file with the name initial_set.txt
# each entry is a space separated list of the following format
# {contract} {attribute} {field} {key1} {key2} ... {keyn} {value}
# for fields that are primitive values it is just {field} {value}
# Also create file initial_meta.txt containing metadata about the fields
# Each metadata entry has the following fields
# {contract} {attribute} {field} {composite key length}
# where {composite key length} is 0 for primitive fields, 1, for mappings, 2 - mappings of mappings, and so on.
def generate_initial_set():
    import random
    num_contracts = 1
    num_attributes = 1
    num_fields = 10
    max_number = 256 # upper bound on numbers generated as keys and values
    min_mapping_size = 1 # minimum number of keys in a mapping
    max_mapping_size = 6 # maximum number of keys in a mapping
    # Assign composite key length to field prefixes
    # 0 means field has a primitive value, 1 - mapping, 2 - mapping of mappings, 3 - mapping of mappings of mapping
    composite_lengths = random.choices([0, 1, 2, 3], weights = [8, 4, 2, 1], k=num_fields)
    with open("initial_set.txt", "w") as f:
        for contract in range(num_contracts):
            for attribute in range(num_attributes):
                for field in range(num_fields):
                    comp_length  = composite_lengths[field]
                    if comp_length == 0:
                        # Just a primitive value, generate
                        v = random.randrange(0, max_number)
                        f.write(f'{contract} {attribute} {field} {v}\n')
                    else:
                        #keys = [random.randrange(0, max_number) for i in range(comp_length)] # components of the current composite key
                        countdown = [random.randrange(min_mapping_size, max_mapping_size) for i in range(comp_length)] # Counting down number of keys that we still need to generate on certain level, 0 means it is done
                        # For each part of the composite key, pre-generate keys by sampling without replacement (to avoid duplicates)
                        key_samples = [random.sample(range(max_number), k=k) for k in countdown]
                        while countdown[0] > 0:
                            # Output field, keys and value
                            f.write(f'{contract} {attribute} {field} ')
                            for i, key_sample in enumerate(key_samples):
                                f.write(f'{key_sample[countdown[i]-1]} ')
                            v = random.randrange(0, max_number)
                            f.write(f'{v}\n')
                            # Move on to the next sequence of keys
                            i = len(countdown) - 1
                            while i >= 0:
                                countdown[i]-=1
                                if countdown[i] > 0:
                                    break
                                if i == 0:
                                    break
                                k = random.randrange(min_mapping_size, max_mapping_size)
                                countdown[i] = k
                                key_samples[i] = random.sample(range(max_number), k=k)
                                i-=1

from dataclasses import dataclass
@dataclass
class WbtNode:
    key: int # node key
    composite: list[int] # composite key of the node
    height: int # maximum length of paths from the node to any leaves
    nesting: int # level of sub-tree nesting (0 - contract, 1 - attribute, 2 - field, 3 - key of the field)
    path: str # path - sequence of 0 (left) or 1 (right) bits specifying how to get from root
    tree: bool # set to True if this node is root of the tree for the nested data structure
    val: int # primitive value for the node (mutually exclusive with subtree)
    subtree: list # complex value for the node (mutually exclusive with val)

# reads initial set from the file initial_set.txt and build initial Wbt tree ensuring it is balanced
def build_initial_tree() -> list[WbtNode]:
    from functools import cmp_to_key
    # read initial set and sort it
    with open("initial_set.txt", "r") as f:
        lines = f.readlines()
    items = [[int(s) for s in line.split()] for line in lines]
    # comparator function to compare composite keys
    def compare(seq1: list[int], seq2: list[int]):
        i = 0
        while i < len(seq1) or i < len(seq2):
            if i >= len(seq1):
                if i >= len(seq2):
                    return 0
                else:
                    return -1
            if i >= len(seq2):
                return 1
            if seq1[i] < seq2[i]:
                return -1
            elif seq1[i] > seq2[i]:
                return 1
            i += 1
        return 0
    items.sort(key=cmp_to_key(compare))
    tree_stack = [[]] # Stack of trees being built, put empty tree on the top
    prefix_stack = [[]] # Stack of the composite key prefixes corresponding to the tree on the tree_stack, put empty prefix on the top
    for item in items:
        num_keys = len(item) - 1
        # check if the prefix of the item matches to the prefix on top of the stack
        while num_keys < len(prefix_stack[-1]) or item[:len(prefix_stack[-1])] != prefix_stack[-1]:
            # tree on the top of the stack is complete, need to pop it
            prefix_stack.pop(-1)
            tree_stack.pop(-1)
        # now check if we need to create nested tree
        while num_keys > len(prefix_stack[-1]) + 1:
            nested_tree = []
            nested_key = item[:len(prefix_stack[-1]) + 1]
            tree_stack[-1].append(WbtNode(key=nested_key[len(prefix_stack[-1])], composite=nested_key, height=0, nesting=len(prefix_stack)-1, path='', tree=True, subtree=nested_tree, val=0)) # depth and path is determined during balancing
            tree_stack.append(nested_tree)
            prefix_stack.append(nested_key)
        # now simply add a new node to the tree which is on top of the tree stack
        tree_stack[-1].append(WbtNode(key=item[len(prefix_stack[-1])], composite=item[:-1], height=0, nesting=len(prefix_stack)-1, path='', tree=False, subtree=None, val=item[-1])) # depth and path is determined during balancing
    main_tree = tree_stack[0]
    return main_tree

# outputs tree as a simple list of nodes
def print_tree(indent: str, nodes: list):
    for node in nodes:
        indent = " " * node.nesting
        if node.tree:
            print(f'{indent}{node.nesting}) {node.key} {node.composite} {node.path}')
        else:
            print(f'{indent}{node.nesting}) {node.key} {node.composite} {node.val} {node.path}')

# splits tree into two subtrees and invokes itself recursively
# for those sub-trees
# the most important "knob" is the choice of the pivot
# the rule we are using for the pivot is as follows
# If binary representation of total number of nodes in the tree starts with `10` (second most significant bit is zero),
# for example, 2, 4, 5, 8, 9, 10, 11, 16, the left subtree is higher than the right subtree, and the size of the left
# subtree is determined by replacing that `10` combination with `01`. For example, for 2 (10), it will be 1 (01),
# for 4 (100) => 2 (010), for 5 (101) => 3 (011), for 8 (1000) => 4 (0100), for 9 (1001) => 5 (0101),
# for 11 (1011) => 7 (0111), for 16 (10000) => 8 (01000). The size of the right subtree can be computed from the
# size of the tree and size of the left subtree.
# If binary representation of total number of nodes in the tree starts `11` (second most significant bit is one),
# for example, 3, 6, 7, 12, 13, 14, 15, the left and the right subtrees are of the equal height. In the case,
# the size of the right subtree is determined by removing the most significant bit from the size of the tree.
# For example, for 3 (11), it will be 1 (1), for 6 (110) => 2 (10), for 7 (111) => 3 (11), for 12 (1100) => 4 (100),
# for 13 (1101) => 5 (101), 14 (1110) => 6 (110), 15 (1111) => 7 (111).
def balance_tree(path: str, nodes: list):
    # Perform balancing purely on the basis of number of element in nodes
    n = len(nodes)
    if n == 0:
        return
    if n == 1:
        pivot = 0
    else:
        # we will shift the value of reduced to the right until it becomes either 2 (10) or 3 (11)
        reduced = n
        fullsize = 0
        while reduced > 3:
            reduced >>= 1
            fullsize = (fullsize << 1) + 1
        if reduced == 3:
            pivot = (fullsize << 1) + 1
        else:
            pivot = n - 1 - fullsize
    if nodes[pivot].tree:
        # nested tree
        nodes[pivot].path = path + 'M'
        balance_tree(path=path+'N', nodes=nodes[pivot].subtree)
    else:
        nodes[pivot].path = path
    balance_tree(path=path+'L', nodes=nodes[:pivot])
    balance_tree(path=path+'R', nodes=nodes[pivot+1:])

def flatten_tree(nodes: list, flat: list):
    for node in nodes:
        flat.append(node)
        if node.tree:
            flatten_tree(node.subtree, flat)

# generates graphical representation of the tree in the graphviz dot format
# input is the tree in the flattened format. Edges between the nodes are derived from the nodes' paths
# therefore the structure is not required anymore
def graph_tree(filename: str, flat: list):
    colors = ['#FDF3D0', '#DCE8FA', '#D9E7D6', '#F1CFCD', '#F5F5F5', '#E1D5E7', '#FFE6CC', 'white']
    with open(filename + ".dot", "w") as f:
        f.write('strict digraph {\n')
        f.write('node [shape=record];\n')
        paths = dict([(node.path, True) for node in flat])
        for node in flat:
            f.write(f'{node.path} [label="{node.key}" style=filled fillcolor="{colors[node.nesting]}"];\n')
            prev = node.path
            dir = ''
            if prev.endswith('M'):
                prev = prev[:-1]
            if prev.endswith('L') or prev.endswith('R'):
                dir = prev[-1]
                prev = prev[:-1]
                if prev != '' and not prev in paths:
                    prev += 'M'
                    assert prev in paths, f'path {prev} not found'
            elif prev.endswith('N'):
                prev = prev[:-1] + 'M'
            if prev != '':
                f.write(f'{prev} -> {node.path}')
                # Show edge direction only if it is L (left) or R (right)
                if dir == 'L' or dir == 'R':
                    f.write(f' [label="{dir}"]')
                f.write(';\n')
        f.write('}\n')

# computes initial merkle hashes and writes resulting tree with intermediate
# hashes into the file initial_hashes.txt
def initial_hash(flat: list):
    with open("initial_hashes.txt", "w") as f:
        empty, root = hash_subtree('', flat, f)
    assert len(empty) == 0, f'unused tree nodes after computing root hash: {len(empty)}'
    return root

def hash_subtree(path: str, nodes: list, f) -> (list, int):
    from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash
    print(f'hash_subtree for {path}, nodes {len(nodes)}')
    if len(nodes) == 0:
        return nodes, 0
    n = nodes[0]
    node_path = n.path
    #print(f'hash_subtree for {path}, nodepath {node_path}')
    if path < node_path and (not node_path.startswith(path)):
        return nodes, 0
    assert path <= node_path, f'incorrect ordering of nodes when computing root hash: {path} > {node_path}'
    if path == node_path:
        nodes = nodes[1:]
    nodes, left_root = hash_subtree(path + 'L', nodes, f)
    nested = False
    if len(nodes) > 0 and nodes[0].path.endswith('M') and path==nodes[0].path[:-1]:
        #print(f'hash_subtree recurse N for {path}, nodepath {nodes[0].path}')
        nn = nodes[0]
        nodes, nested_root = hash_subtree(path + 'N', nodes[1:], f)
        nested = True
        l_hash = pedersen_hash(left_root, nn.key)
    else:
        l_hash = pedersen_hash(left_root, n.key)
    nodes, right_root = hash_subtree(path + 'R', nodes, f)
    if nested:
        r_hash = pedersen_hash(nested_root, right_root)
    else:
        r_hash = pedersen_hash(n.val, right_root)
    root = pedersen_hash(l_hash, r_hash)
    if nested:
        f.write(f'{path}M {root} {" ".join([str(k) for k in nn.composite])}\n')
    else:
        f.write(f'{path} {root} {" ".join([str(k) for k in n.composite])} {n.val}\n')
    return nodes, root

# Reads tree from the file produced by the initial_hash function
def read_from_file(filename: str) -> list:
    with open(filename, "r") as f:
        lines = f.readlines()
    items = [[s for s in line.split()] for line in lines]
    print(items)
    return []

# randomly selects some nodes from the tree, and also generates some missing nodes
def select_reads(nodes: list, exist_amount: int, miss_amount: int) -> list:
    import random
    exist_idx = random.sample(range(len(nodes)), k=exist_amount)
    result = [nodes[idx].composite for idx in exist_idx]
    dedup = {}
    for r in result:
        dedup[str(r)] = True
    miss_idx = random.sample(range(len(nodes)), k=miss_amount)
    # some of the missing nodes might accidentally be present, but it is ok
    for idx in miss_idx:
        key = nodes[idx].composite.copy()
        key[-1] += 1
        key_str = str(key)
        if not key_str in dedup:
            dedup[key_str] = True
            result.append(key)
    return result

def hash_check():
    from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash
    x = 1
    y = 0
    z = pedersen_hash(x, y)
    print(z)

#generate_initial_set()
tree = build_initial_tree()

# Now balance every sub tree to establish correct depth and path values
balance_tree(path='', nodes=tree)

flat = []
flatten_tree(tree, flat)
flat.sort(key=lambda n: n.path)
print_tree("", flat)

graph_tree('initial_graph', flat)
import subprocess
subprocess.call(['dot', '-Tpng', 'initial_graph.dot', '-o', 'initial_graph.png'])

root = initial_hash(flat=flat)
print(f'initial root hash: {root}')

read_from_file('initial_hashes.txt')

reads = select_reads(nodes=flat, exist_amount=4, miss_amount=1)
print(f'selected reads: {reads}')

