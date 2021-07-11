# Operations with AVL trees

from dataclasses import dataclass
from functools import cmp_to_key
import random
import subprocess

# generates initial set of composite keys and correcsponding values pseudorandomly, given initial setting
# it writes the initial set into a file with the name initial_set.txt
# each entry is a space separated list of the following format
# {contract} {attribute} {field} {key1} {key2} ... {keyn} {value}
# for fields that are primitive values it is just {field} {value}
def generate_initial_set():
    num_contracts = 1
    num_attributes = 1
    num_fields = 10
    max_number = 256 # upper bound on numbers generated as keys and values
    min_mapping_size = 1 # minimum number of keys in a mapping
    max_mapping_size = 4 # maximum number of keys in a mapping
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

@dataclass
class AvlNode:
    key: list # potentially composite key
    depth: int # length of path from root of the tree to 
    path: str # path - sequence of 0 (left) or 1 (right) bits specifying how to get from root
    tree: bool # set to True if this node is root of the tree for the nested data structure
    val: int # primitive value for the node (mutually exclusive with subtree)
    subtree: list # complex value for the node (mutually exclusive with val)

# reads initial set from the file initial_set.txt and build initial avl tree ensuring it is balanced
def build_initial_tree():
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
            tree_stack[-1].append(AvlNode(key=nested_key, depth=0, path='', tree=True, subtree=nested_tree, val=0)) # depth and path is determined during balancing
            tree_stack.append(nested_tree)
            prefix_stack.append(nested_key)
        # now simply add a new node to the tree which is on top of the tree stack
        tree_stack[-1].append(AvlNode(key=item[:num_keys], depth=0, path='', tree=False, subtree=None, val=item[-1])) # depth and path is determined during balancing
    main_tree = tree_stack[0]
    print_tree("", main_tree)
    # Now balance every sub tree to establish correct depth and path values
    balance_tree(depth=0, path='x', nodes=main_tree)
    graph_tree('initial_graph', main_tree)
    subprocess.call(['dot', '-Tpng', 'initial_graph.dot', '-o', 'initial_graph.png'])

def print_tree(indent: str, nodes: list):
    for node in nodes:
        if node.tree:
            print(f'{indent}{node.key}')
            print_tree(indent+"  ", node.subtree)
        else:
            print(f'{indent}{node.key} {node.val}')

def balance_tree(depth: int, path: str, nodes: list):
    # Perform balancing purely on the basis of number of element in nodes
    if len(nodes) == 0:
        return
    pivot = len(nodes)//2
    nodes[pivot].depth = depth
    nodes[pivot].path = path
    if nodes[pivot].tree:
        # nested tree
        balance_tree(depth=depth, path=path+'x', nodes=nodes[pivot].subtree)
    balance_tree(depth=depth+1, path=path+'0', nodes=nodes[:pivot])
    balance_tree(depth=depth+1, path=path+'1', nodes=nodes[pivot+1:])

def flatten_tree(nodes: list, flat: list):
    for node in nodes:
        flat.append(node)
        if node.tree:
            flatten_tree(node.subtree, flat)

def graph_tree(filename: str, nodes: list):
    flat = []
    flatten_tree(nodes, flat)

    with open(filename + ".dot", "w") as f:
        f.write('strict digraph {\n')
        f.write('node [shape=record];\n')
        for node in flat:
            label = '|'.join([str(k) for k in node.key])
            f.write(f'{node.path} [label="{label}"];\n')
            if node.path != 'x':
                f.write(f'{node.path[:-1]} -> {node.path}')
                if node.path[-1] != 'x':
                    f.write(f' [label="{node.path[-1]}"]')
                f.write(';\n')
                
        f.write('}\n')

generate_initial_set()
build_initial_tree()
