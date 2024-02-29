import json
import pickle
import time
import sys
import argparse

import random
import numpy as np

import leakage_processing
import attack_util as util
import attack_candidates


# Get log-likelihood for one particular sequence of tokens
def get_log_likelihood(tokens, assignments, string_freq, auxiliary_freq):
    string = ''
    for token in tokens:
        string += assignments[token]

    log_likelihood = 0
    if string in auxiliary_freq:
        log_likelihood = string_freq[tokens] * np.log(auxiliary_freq[string]) - auxiliary_freq[string]
    else:
        log_likelihood = -1000

    return log_likelihood




# Initial solution. Fully randomised for now
def initial_solution_frequency(string_freq, candidates_token_seq):
    assignments = {}

    for tokens in sorted(string_freq.keys(), key=lambda x:string_freq[x]):
        candidate_string = random.choice(candidates_token_seq[tokens])

        for token, char in zip(tokens, candidate_string):
            assignments[token] = char

    return assignments



# Find a neighbourhood solution, based on a sequence of tokens as opposed to a single token
def neighbour_candidates(string_freq_keys, candidates_token, candidates_token_seq):
    # sample token sequence from string_freq_keys
    # string_freq_keys only contains token sequences that have multiple candidates in candidates_token_seq
    tokens = random.choice(string_freq_keys)
    guesses = random.choice(candidates_token_seq[tokens])

    guess = {}
    for token, _guess in zip(tokens, guesses):
        guess[token] = _guess
    return tokens, guess




# Main attack routine
def attack(candidates_token, candidates_token_seq, string_freq, auxiliary_freq, N_iter):
    scores = {}

    # get the tokens to update for each token sequence
    tokens_to_update_single = {}
    for tokens in string_freq:
        for token in tokens:
            if token not in tokens_to_update_single:
                tokens_to_update_single[token] = []
            tokens_to_update_single[token] += [tokens]

    
    tokens_to_update = {}
    for tokens in string_freq:
        tokens_to_update[tokens] = set()
        for token in tokens:
            tokens_to_update[tokens].update(tokens_to_update_single[token])
            

    # Get intial assignment and its likelihood score
    time_start = time.time()
    assignments = initial_solution_frequency(string_freq, candidates_token_seq)
    time_end = time.time()
    
    print("Initial solution found: %.2f s." % (time_end - time_start))

    # Calculate initial score
    time_start = time.time()
    score = {}
    for tokens in string_freq:
        score[tokens] = get_log_likelihood(tokens, assignments, string_freq, auxiliary_freq)
    time_end = time.time()
    print("Initial score computed: %.2f s." % (time_end - time_start))


    #  Try to improve the guess
    time_start = time.time()

    # Gather all token sequences with more than one candidates in candidates_token_seq
    string_freq_keys = []
    choice_weights   = []
    for tokens in string_freq:
        if len(candidates_token_seq[tokens]) > 1:
            string_freq_keys += [tokens]
            
    
    for n_iter in range(N_iter):
        if n_iter % (N_iter // 10) == 0:
            print("Main attack progress: %d%%,\t" % (n_iter*100/N_iter), end="")
            current_score = sum([score[tokens] for tokens in score])
            print("Current score: %.3f" % current_score)

        if n_iter % (N_iter // 100) == 0:
            current_score = sum([score[tokens] for tokens in score])
            scores[n_iter] = current_score
        
        # Make new guess
        tokens_guess, guess = neighbour_candidates(string_freq_keys, candidates_token, candidates_token_seq)
        assignments_old = {}
        for token in guess:
            assignments_old[token]  = assignments[token]
            assignments[token]       = guess[token]
        
        # Calculate likelihood delta
        score_delta = 0
        score_delta_dict = {}
        for tokens in tokens_to_update[tokens_guess]:
            score_delta_dict[tokens] = get_log_likelihood(tokens, assignments, string_freq, auxiliary_freq)
            score_delta += score_delta_dict[tokens]
            score_delta -= score[tokens]

        # Update the assignment if the score improves
        if score_delta > 0:
            for tokens in score_delta_dict:
                score[tokens] = score_delta_dict[tokens]
        else:
            for token in guess:
                assignments[token] = assignments_old[token]

    time_end = time.time()
    print("Main attack done: %.2f s (%.2f ms per iteration)." % (time_end - time_start, (time_end - time_start)*(10**3)/N_iter))
    
    return assignments, scores



    



if __name__ == "__main__":
    # parsing arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--genome', action='store_true', dest='genome', required=False, help="Use this flag to run attacks on the genome dataset.")
    parser.add_argument('--ndoc', action='store', type=int, dest='ndoc', required=True, help="The number of documents used as the target of the attack.")
    parser.add_argument('--nqry', action='store', type=int, dest='nqry', required=True, help="The number of queries used to generate the leakage.")
    parser.add_argument('--index', action='store', type=int, dest='index', required=False, help="The index of the leakage. Default is 0.")
    parser.add_argument('--niter', action='store', type=int, dest='niter', required=False, help="The number of interations of simulated annealing. Default is 2*10^7.")
    parser.add_argument('--nrun', action='store', type=int, dest='nrun', required=False, help="The number of runs on each copy. Default is 1.")
    parser.add_argument('--offset', action='store', type=int, dest='offset', required=False, help="Offset to <index>. Used for leakage files and reports only.")
    parser.add_argument('--pre-leakage', action='store_true', dest='pre_leakage', required=False, help="Use precomputed leakage if the flag is set.")
    parser.add_argument('--pre-candidates', action='store_true', dest='pre_candidates', required=False, help="Use precomputed candidates if the flag is set.")
    args = parser.parse_args(sys.argv[1:])

    # set arguments
    target_dir = 'enWiki'
    if args.genome == True:
        target_dir = 'genome'
    N_index = 0
    if args.index != None:
        N_index = args.index
    N_iter = 2*10**7
    if args.niter != None:
        N_iter = args.niter
    N_run = 1
    if args.nrun != None:
        N_run = args.nrun
    pre_computed_leakage = False
    if args.pre_leakage != None:
        pre_computed_leakage = args.pre_leakage
    pre_computed_candidates = False
    if args.pre_candidates != None:
        pre_computed_candidates = args.pre_candidates
    

    # set file paths
    file_name_input1 = f'../raw_data/{target_dir}/{target_dir}_target_{args.ndoc}_{N_index}.json'
    file_name_input2 = f'../leakage_output/{target_dir}/'
    file_name_output = f'../results/{target_dir}/'

    if args.genome == True:
        file_name_input1 = f'../raw_data/{target_dir}/{target_dir}_target_{args.ndoc}_0.json'



    # Load plaintexts
    file_input = open(file_name_input1, 'r', encoding='utf-8')
    texts_json = json.load(file_input)
    file_input.close()
    texts = [text.lower() for text in texts_json]
    texts_len_total = sum([len(text) for text in texts])


    # overwrite index
    if args.offset != None:
        N_index += args.offset

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
    if pre_computed_leakage == True:
        char_equality_group, char_equality_inv, prefix_equality_dict = util.load_leakage_from_file(file_name_input2, args.ndoc, args.nqry, N_index)
    else:
        prefix_equality_dict = leakage_processing.extract_prefix_equality(leakage_dict)
        print("Prefix equality computed.")
        char_equality_group, char_equality_inv = leakage_processing.extract_character_equality(leakage_dict, prefix_equality_dict)
        print("Character equality extracted.")
        util.save_leakage_to_file(char_equality_group, char_equality_inv, prefix_equality_dict, file_name_input2, args.ndoc, args.nqry, N_index)
        print("Processed leakage saved.")

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

    sigma, N_filter = 7, 3
    if args.genome == True:
        sigma, N_filter = 5, 2


    # get candidates for each token
    time_start = time.time()
    if pre_computed_candidates == True:
        candidates_token, candidates_token_seq = util.load_candidates_from_file(file_name_input2, args.ndoc, args.nqry, N_index)
    else:
        candidates_token, candidates_token_seq = attack_candidates.find_token_candidates(char_equality_group, leakage_tree, leakage_level, string_freq, id_to_leakage_tokens_map, auxiliary_freq, set(char_list))
        util.save_candidates_to_file(candidates_token, candidates_token_seq, file_name_input2, args.ndoc, args.nqry, N_index)
    time_end = time.time()
    print("Candidates found: %.2f s." % (time_end - time_start))

    for run_index in range(N_run):
        assignments, scores = attack(candidates_token, candidates_token_seq, string_freq, auxiliary_freq, N_iter)
        util.report(assignments, scores, leakage_dict, char_equality_group, candidates_token, texts, file_name_output, string_freq, leakage_tokens_to_id_map, args.ndoc, args.nqry, N_index, run_index)

    
