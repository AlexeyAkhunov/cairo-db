# Operations with AVL trees

from dataclasses import dataclass
import random

# generates initial set of composite keys and correcsponding values pseudorandomly, given initial setting
# it writes the initial set into a file with the name initial_set.txt
# each entry is a space separated list of the following format
# {field} {key1} {key2} ... {keyn} {value}
# for fields that are primitive values it is just {field} {value}
def generate_initial_set():
    num_fields = 100
    max_number = 256 # upper bound on numbers generated as keys and values
    min_mapping_size = 1 # minimum number of keys in a mapping
    max_mapping_size = 10 # maximum number of keys in a mapping
    # Assign composite key length to field prefixes
    # 0 means field has a primitive value, 1 - mapping, 2 - mapping of mappings, 3 - mapping of mappings of mapping
    composite_lengths = random.choices([0, 1, 2, 3], weights = [8, 4, 2, 1], k=num_fields)
    with open("initial_set.txt", "w") as f:
        for field in range(num_fields):
            comp_length  = composite_lengths[field]
            if comp_length == 0:
                # Just a primitive value, generate
                v = random.randrange(0, max_number)
                f.write(f'{field} {v}\n')
            else:
                keys = [random.randrange(0, max_number) for i in range(comp_length)] # components of the current composite key
                countdown = [random.randrange(min_mapping_size, max_mapping_size) for i in range(comp_length)] # Counting down number of keys that we still need to generate on certain level, 0 means it is done
                while countdown[0] > 0:
                    # Output field, keys and value
                    f.write(f'{field} ')
                    for k in keys:
                        f.write(f'{k} ')
                    v = random.randrange(0, max_number)
                    f.write(f'{v}\n')
                    # Move on to the next sequence of keys
                    i = len(countdown) - 1
                    while i >= 0:
                        countdown[i]-=1
                        keys[i] = random.randrange(0, max_number)
                        if countdown[i] > 0:
                            break
                        if i == 0:
                            break
                        countdown[i] = random.randrange(min_mapping_size, max_mapping_size)
                        i-=1
                f.write(f'{field} {composite_lengths[field]}\n')

@dataclass
class AvlItem:
    key: list # potentially composite key
    val: int
    # hint for encoding the structure of the tree. Assuming that the tree is built from the sorted
    # sequence of keys using stack based algorith, branches specifies how many times, after this
    # node is pushed to the stack, two nodes need to be taken from the stack and connected
    # via branch that is put back onto the stack
    branches: int

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
    sorted_items = sorted(items, cmp=compare)

#generate_initial_set()
build_initial_tree()