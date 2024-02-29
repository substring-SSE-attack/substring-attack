import json
import pickle

import time



class Node:
    # basic setup
    def __init__(self):
        self.data = None
        self.leafCount = 0
        self.edges = []
        self.children = []


    def insert_child(self, edge, node):
        self.edges += [edge]
        self.children += [node]


    # count the number of leaf nodes for each node
    def update_leaf_count(self):
        if len(self.children) == 0:
            self.leafCount = len(self.data)
            return self.leafCount

        leafCounts = []
        for child in self.children:
            leafCounts += [child.update_leaf_count()]
        self.leafCount = sum(leafCounts) + self.leafCount
        return self.leafCount 
            
        

    # travesal subroutines
    def traverse_node_by_index(self, index):
        return self.children[index]

    # WARNING: deprecated
    def traverse_node_by_edge(self, edge):
        index = self.edges.index(edge)
        return self.children[index]

    # visualisation
    def visualise(self, depth=0, index=0):
        if len(self.edges) == 0:
            print(self.data)
            return
        
        for index in range(len(self.edges)):
            if index != 0 and depth >0:
                print('-'*depth, end='')
            print('-' + self.edges[index], end='')
            self.children[index].visualise(depth=depth+1+len(self.edges[index]),index=index)



class SuffixTree:
    def __init__(self, strings, printing=True):
        self.tree = Node()
        self.strings = strings
        self.printing = printing

        # build a suffix tree on the fly
        for index_str in range(len(strings)):
            string = strings[index_str] + '$'
            for index_pos in range(len(string)):
            #for index_pos in range(5):
                self.add_suffix(self.tree, string[index_pos:], index_str, index_pos, index_pos)

            #if printing == True and index_str % (len(strings) / 20) == 0:
            #    print(f"Adding string {index_str} / {len(strings)}")
            if printing == True:
                print(f"Adding string {index_str} / {len(strings)}")

            

        # compress it to make it a suffix tree
        self.tree.update_leaf_count()
        if printing == True:
            print("Leaf counts updated")


    def add_suffix(self, current_node, string, index_str, index_pos, current_pos):
        edge_idx, edge_len = -1, -1
        for edge_idx_tmp in range(len(current_node.edges)):
            edge_data = current_node.edges[edge_idx_tmp]
            current_edge = self.strings[edge_data[0]][edge_data[1]:edge_data[2]]
            for edge_len_tmp in range(1, min(len(string), len(current_edge))+1):
                if string[:edge_len_tmp] == current_edge[:edge_len_tmp]:
                    edge_len = edge_len_tmp
                else:
                    break
            if edge_len > 0:
                edge_idx = edge_idx_tmp
                break
            

        # Case 1: no substring of the string is a substring of one of the edges of the current node
        if edge_idx == -1:
            node = Node()
            node.data = [(index_str, index_pos)]
            edge_data = (index_str, current_pos, current_pos+len(string))
            current_node.insert_child(edge_data, node)


        # Case 2: one of the edges perfectly matches the string
        elif edge_idx >= 0 and edge_len == len(string):
            if current_node.traverse_node_by_index(edge_idx).data == None:
                current_node.traverse_node_by_index(edge_idx).data = [(index_str, index_pos)]
            else:
                current_node.traverse_node_by_index(edge_idx).data += [(index_str, index_pos)]


        # Case 3: there is a partial match between the string and one of the edges
        elif edge_idx >= 0 and edge_len < len(string) and edge_len < current_node.edges[edge_idx][2] - current_node.edges[edge_idx][1]:
            edge_share = string[:edge_len]
            edge_old = current_node.edges.pop(edge_idx)
            node_old = current_node.children.pop(edge_idx)

            edge_share_data = (edge_old[0], edge_old[1], edge_old[1]+edge_len)
            edge_split_data = (edge_old[0], edge_old[1]+edge_len, edge_old[2])


            #if edge_share == 'e':
            #    print(edge_old)
            #    print(edge_share_data)
            #    print(edge_split_data)

            node_new = Node()

            current_node.insert_child(edge_share_data, node_new)
            current_node_tmp = current_node.traverse_node_by_index(-1)

            current_node_tmp.insert_child(edge_split_data, node_old)
            self.add_suffix(current_node_tmp, string[edge_len:], index_str, index_pos, current_pos+edge_len)

        # Case 4: the edge fully matches part of the string 
        elif edge_idx >= 0 and edge_len == current_node.edges[edge_idx][2] - current_node.edges[edge_idx][1]:
            current_node_tmp = current_node.traverse_node_by_index(edge_idx)
            self.add_suffix(current_node_tmp, string[edge_len:], index_str, index_pos, current_pos+edge_len)


    def match(self, word):
        word_current = word
        node = self.tree
        matched_edges = []


        
        while len(word_current) > 0:
            # parse edges into concrete edges
            edge_indices = node.edges
            edges = []
            for edge_index in edge_indices:
                edges += [self.strings[edge_index[0]][edge_index[1]:edge_index[2]]]


            # find the edge to traverse
            match_flag = False
            for edge_idx in range(len(edges)):
                match_len = 0
                while match_len < min(len(word_current), len(edges[edge_idx])) and word_current[match_len] == edges[edge_idx][match_len]:
                    match_len += 1

                # case 1: word_current is a substring of an edge, report full match
                if match_len == len(word_current):
                    word_current = word_current[match_len:]
                    matched_edges += [edge_indices[edge_idx]]
                    node = node.traverse_node_by_index(edge_idx)
                    match_flag = True
                    break

                # case 2: a substring of word_current matches with an edge, move forward
                elif match_len > 0 and match_len < len(word_current):
                    word_current = word_current[match_len:]
                    matched_edges += [edge_indices[edge_idx]]
                    node = node.traverse_node_by_index(edge_idx)
                    match_flag = True
                    break

                
            # case 3: it is possible that no edge matches with the current word. Return None in that case
            if match_flag == False:
                return None

        return matched_edges, node.leafCount



        

