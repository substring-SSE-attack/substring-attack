import sys
import pickle
import random

from suffix_tree import Node, SuffixTree


def get_auxiliary_info(string, str_len, node, data):
    if len(string) + 1 > str_len[1]:
        return

    for edge_idx in range(len(node.edges)):
        edge = node.edges[edge_idx]
        if edge[2] > len(data.strings[edge[0]]):
            edge = (edge[0], edge[1], edge[2]-1)
        if edge[1] == edge[2]:
            continue
        
        edge_str = data.strings[edge[0]][edge[1]:edge[2]]
        node_new = node.traverse_node_by_index(edge_idx)
        
        if len(string) + 1 >= str_len[0]:
            string_freq[string+edge_str[0]] = node_new.leafCount


        proceed = True
        for char in edge_str:
            if char not in char_set:
                proceed = False

        if proceed == True:
            get_auxiliary_info(string+edge_str, str_len, node_new, data)




sys.setrecursionlimit(20000)

file_input = open('../suffix_trees/suffix_tree_genome_aux', 'rb')
data = pickle.load(file_input)
file_input.close()


# Global variables
string_freq = {}

char_set = ['a', 'c', 'g', 't']
char_set = set(char_set)

# Get auxiliary info
str_len = [0, 12]
get_auxiliary_info("", str_len, data.tree, data)

# Get total string length
texts_len = sum([len(x)-1 for x in data.strings])
string_freq[-1] = texts_len


# Output leakage to file
file_output = open('../leakage_output/genome/auxiliary.pkl', 'wb')
pickle.dump(string_freq, file_output)
file_output.close()


'''
for string in sorted(string_freq.keys(), key=lambda x: string_freq[x], reverse=True):
    if string_freq[string] > 1000:
        print(string, string_freq[string])
'''
