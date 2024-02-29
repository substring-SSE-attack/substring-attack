import json
import pickle
import time
import sys
import argparse

import random
import numpy as np

import leakage_processing
import attack_candidates



if __name__ == "__main__":
    # parsing arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--genome', action='store_true', dest='genome', required=False, help="Use this flag to run analysis on the genome dataset.")
    parser.add_argument('--ndoc', action='store', type=int, dest='ndoc', required=True, help="The number of documents used as the target of the attack.")
    parser.add_argument('--nqry', action='store', type=int, dest='nqry', required=True, help="The number of queries used to generate the leakage.")
    parser.add_argument('--index', action='store', type=int, dest='index', required=False, help="The index of the leakage. Default is 0.")
    args = parser.parse_args(sys.argv[1:])

    # set arguments
    target_dir = 'enWiki'
    if args.genome == True:
        target_dir = 'genome'
        
    N_index = 0
    if args.index != None:
        N_index = args.index
    

    # set file paths
    file_name_input1 = f'../raw_data/{target_dir}/{target_dir}_target_{args.ndoc}_{N_index}.json'
    file_name_input2 = f'../leakage_output/{target_dir}/'
    file_name_output = f'../results_parameters/{target_dir}/'

    if args.genome == True:
        file_name_input1 = f'../raw_data/{target_dir}/{target_dir}_target_1_0.json'

    # Load plaintexts
    file_input = open(file_name_input1, 'r', encoding='utf-8')
    texts_json = json.load(file_input)
    file_input.close()
    texts = [text.lower() for text in texts_json]
    texts_len_total = sum([len(text) for text in texts])


    # Load leakage from file
    file_input = open(file_name_input2 + f'leakage_{args.ndoc}_{args.nqry}_{N_index}.pkl', 'rb')
    leakage_dict = pickle.load(file_input)
    file_input.close()

    file_input = open(file_name_input2 + f'edge_map_{args.ndoc}_{args.nqry}_{N_index}.pkl', 'rb')
    map_edge_to_id = pickle.load(file_input)
    file_input.close()

    map_id_to_edge = {}
    for edge in map_edge_to_id:
        map_id_to_edge[map_edge_to_id[edge]] = edge

    print('Data loading done.')

    '''
    # Run the attack
    '''
    # Processing leakage
    time_start = time.time()
    prefix_equality_dict = leakage_processing.extract_prefix_equality(leakage_dict)
    print("Prefix equality computed.")
    char_equality_group, char_equality_inv = leakage_processing.extract_character_equality(leakage_dict, prefix_equality_dict)
    print("Character equality extracted.")

    string_freq, leakage_tokens_to_id_map, id_to_leakage_tokens_map = leakage_processing.extract_string_frequency(leakage_dict, char_equality_inv)
    leakage_tree, leakage_level = leakage_processing.extract_leakage_tree(leakage_dict, id_to_leakage_tokens_map)


    # Load auxiliary substring frequency
    file_input = open(file_name_input2 + 'auxiliary.pkl', 'rb')
    auxiliary_freq = pickle.load(file_input)
    file_input.close()
    auxiliary_freq_total = auxiliary_freq[-1]
    del auxiliary_freq[-1]
    for key in auxiliary_freq:
        auxiliary_freq[key] *= texts_len_total / auxiliary_freq_total

    print("Leakage processing done.")
    time_end = time.time()
    print("Time taken: %.2f s" % (time_end-time_start))



    # Define valid characters
    char_list = [' ', '-', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

    if args.genome == True:
        char_list = ['a', 'c', 'g', 't']


    # Define the range of parameters to be searched over
    sigma_range = [3,4,5,6,7]
    N_filter_range = [3,4,5,6,7,8]
    if args.genome == True:
        sigma_range = [3,4,5,6,7]
        N_filter_range = [1,2,3]

    # get candidates for each token
    for sigma in sigma_range:
        for N_filter in N_filter_range:
            time_start = time.time()
            candidates_token, candidates_token_seq = attack_candidates.find_token_candidates(char_equality_group, leakage_tree, leakage_level, string_freq, id_to_leakage_tokens_map,
                                                                                             auxiliary_freq, set(char_list), sigma=sigma, N_filter=N_filter)
            time_end = time.time()
            print("Candidates found: %.2f s." % (time_end - time_start))

            size_recon_space = 0
            for cand in candidates_token_seq:
                size_recon_space += np.log10(len(candidates_token_seq[cand]))

            N_hits = 0
            for cand in candidates_token_seq:
                token_id = leakage_tokens_to_id_map[cand]
                query_real = leakage_dict[token_id]['query_str']
                if query_real in candidates_token_seq[cand]:
                    N_hits += 1

            file_output = open(file_name_output + f"report_{args.ndoc}_{args.nqry}_{sigma}_{N_filter}_{N_index}.txt", "w")
            file_output.write(str(size_recon_space) + "\n")
            file_output.write(str(N_hits) + "," + str(len(candidates_token_seq)) + "\n")
            file_output.close()

    
    

    
