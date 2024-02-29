import pickle
import random
import sys
import argparse
import time

from suffix_tree import Node, SuffixTree


def update_leakage_dict(edges, leafCount=None):
    global edge_id_ctr
    
    if tuple(edges) in map_edge_to_id:
        edge_id = map_edge_to_id[tuple(edges)]
        return edge_id

    # Assign edge id
    map_edge_to_id[tuple(edges)] = edge_id_ctr
    

    str_len = 0
    for edge in edges[:-1]:
        str_len += edge[2] - edge[1]

    leakage_dict[edge_id_ctr] = {
            'str_len':  str_len+1,}

    if leafCount != None:
        leakage_dict[edge_id_ctr]['leafCount'] = leafCount


    edge_id_ctr += 1
    
    return map_edge_to_id[tuple(edges)]
    

def update_leakage(word, data):
    for char in word:
        if char not in char_set:
            return
    
    result = data.match(word)
    if result == None:
        return

    edges = result[0]
    leafCount = result[1]

    leakage_ids = []
    for ii in range(1, len(edges)+1):
        id_new = update_leakage_dict(edges[:ii])
        leakage_ids += [id_new]

        leakage_dict[id_new]['prefix'] = leakage_ids[:-1]

    leakage_dict[id_new]['query_str'] = word
    id_new = update_leakage_dict(edges)
    leakage_dict[id_new]['str_idx'] = (edges[-1][0], edges[-1][1] - leakage_dict[id_new]['str_len']+1)
    leakage_dict[id_new]['leafCount'] = leafCount


def generate_leakage(N_queries, str_len, data):
    word_set = set()
    
    for query_idx in range(N_queries):
        good_word_flag = False
        while good_word_flag == False:
            str_idx = random.randrange(len(data.strings))
            while len(data.strings[str_idx]) == 0:
                str_idx = random.randrange(len(data.strings))
            pos_start = random.randrange(len(data.strings[str_idx]))
            pos_end = pos_start + random.randrange(str_len[0], str_len[1])

            word = data.strings[str_idx][pos_start:pos_end]        
            result = data.match(word)
    
            if result[1] > 100 and len(word) >= str_len[0] and pos_end < len(data.strings[str_idx]) - 1 and word not in word_set:
                good_word_flag = True
            if word[0] == ' ':
                good_word_flag = False
            
        update_leakage(word, data)
        word_set.add(word)

        if query_idx % (N_queries//10) == 0:
            print(f"Progress: {query_idx} / {N_queries}")



# Global variables
str_len = [3, 12]
edge_id_ctr = 0
map_edge_to_id = {}
leakage_dict = {}

char_set = [' ', '-', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
            'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
char_set = set(char_set)


if __name__ == "__main__":
    # parsing arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--ndoc', action='store', type=int, dest='ndoc', required=True, help="The number of documents used as the target of the attack. These documents do not overlap with the auxiliary documents and they are randomly picked.")
    parser.add_argument('--ncopy', action='store', type=int, dest='ncopy', required=True, help="The number of copies of target documents to produce. Each copy is independently sampled.")
    parser.add_argument('--nqry', action='store', type=int, dest='nqry', required=True, help="The number of non-repeating queries generated.")
    parser.add_argument('--len', action='store', type=str, dest='len', required=False, help="The length of the strings generated for the queries. The input has the format a,b.")
    parser.add_argument('--offset', action='store', type=int, dest='offset', required=False, help="If specified, the leakage output will use <ncopy+offset> instead of <ncopy>.")
    parser.add_argument('--g1', action='store_true', dest='g1', required=False, help="If the flag is used, generate only one leakage specified by <ncopy>.")
    args = parser.parse_args(sys.argv[1:])

    if args.len != None:
        str_len[0] = int(args.len.split(',')[0])
        str_len[1] = int(args.len.split(',')[1])

    if args.g1 == False:
        for target_idx in range(args.ncopy):
            edge_id_ctr = 0
            map_edge_to_id = {}
            leakage_dict = {}

            time_start = time.time()
            
            file_input = open(f'../suffix_trees/suffix_tree_enWiki_{args.ndoc}_{target_idx}', 'rb')
            data = pickle.load(file_input)
            file_input.close()

            generate_leakage(args.nqry, str_len, data)

            if args.offset != None:
                target_idx += args.offset

            file_output = open(f'../leakage_output/enWiki/leakage_{args.ndoc}_{args.nqry}_{target_idx}.pkl', 'wb')
            pickle.dump(leakage_dict, file_output)
            file_output.close()

            file_output = open(f'../leakage_output/enWiki/edge_map_{args.ndoc}_{args.nqry}_{target_idx}.pkl', 'wb')
            pickle.dump(map_edge_to_id, file_output)
            file_output.close()

            print(f"Leakage generation for the {target_idx+1}-th target suffix tree complete.")
            print("Time taken: %.2f s." % (time.time() - time_start))
    else:
        target_idx = args.ncopy
        edge_id_ctr = 0
        map_edge_to_id = {}
        leakage_dict = {}

        time_start = time.time()
        
        file_input = open(f'../suffix_trees/suffix_tree_enWiki_{args.ndoc}_{target_idx}', 'rb')
        data = pickle.load(file_input)
        file_input.close()

        generate_leakage(args.nqry, str_len, data)

        if args.offset != None:
            target_idx += args.offset

        file_output = open(f'../leakage_output/enWiki/leakage_{args.ndoc}_{args.nqry}_{target_idx}.pkl', 'wb')
        pickle.dump(leakage_dict, file_output)
        file_output.close()

        file_output = open(f'../leakage_output/enWiki/edge_map_{args.ndoc}_{args.nqry}_{target_idx}.pkl', 'wb')
        pickle.dump(map_edge_to_id, file_output)
        file_output.close()

        print(f"Leakage generation for the {target_idx+1}-th target suffix tree complete.")
        print("Time taken: %.2f s." % (time.time() - time_start))
        
