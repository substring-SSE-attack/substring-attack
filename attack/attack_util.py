import pickle
import json

def load_leakage_from_file(file_name_input, N_docs, N_qry, N_index):
    file_input = open(file_name_input + f'processed_leakage_{N_docs}_{N_qry}_{N_index}.pkl', 'rb')
    char_equality_group, char_equality_inv, prefix_equality_dict = pickle.load(file_input)
    file_input.close()

    return char_equality_group, char_equality_inv, prefix_equality_dict


def save_leakage_to_file(char_equality_group, char_equality_inv, prefix_equality_dict, file_name_output,N_docs, N_qry, N_index):
    leakage = char_equality_group, char_equality_inv, prefix_equality_dict
    file_out = open(file_name_output + f'processed_leakage_{N_docs}_{N_qry}_{N_index}.pkl', 'wb')
    pickle.dump(leakage, file_out)
    file_out.close()


def load_candidates_from_file(file_name_input, N_docs, N_qry, N_index):
    file_input = open(file_name_input + f'candidates_{N_docs}_{N_qry}_{N_index}.pkl', 'rb')
    candidates_token, candidates_token_seq = pickle.load(file_input)
    file_input.close()

    return candidates_token, candidates_token_seq


def save_candidates_to_file(candidates_token, candidates_token_seq, file_name_output, N_docs, N_qry, N_index):
    candidates = candidates_token, candidates_token_seq
    file_out = open(file_name_output + f'candidates_{N_docs}_{N_qry}_{N_index}.pkl', 'wb')
    pickle.dump(candidates, file_out)
    file_out.close()


def report(assignments, scores, leakage_dict, char_equality_group, candidates_token, texts, file_name_output, string_freq, leakage_tokens_to_id_map, N_doc, N_qry, N_index, run_index):
    N_correct = 0
    N_correct_seq = 0
    N_correct_seq_long, N_seq_long = 0, 0
    N_correct_full = 0
    N_coverage, N_coverage_total = 0, 0
    
    for token in assignments:
        leakage_idx = list(char_equality_group[token])[0]
        str_idx     = leakage_dict[leakage_idx[0]]['str_idx']
        
        char_guess = assignments[token]
        char_real  = texts[str_idx[0]][str_idx[1]+leakage_idx[1]]

        if char_guess == char_real:
            N_correct += 1
            N_coverage += len(char_equality_group[token])
        

        N_coverage_total += len(char_equality_group[token])


    for tokens in string_freq:
        leakage_id = leakage_tokens_to_id_map[tokens]
        str_query = leakage_dict[leakage_id]['query_str']
        
        str_guess, str_real = "", ""
        for token in tokens:
            leakage_idx = list(char_equality_group[token])[0]
            str_idx     = leakage_dict[leakage_idx[0]]['str_idx']
            
            char_guess = assignments[token]
            char_real  = texts[str_idx[0]][str_idx[1]+leakage_idx[1]]

            str_guess   += char_guess
            str_real    += char_real
        
        if str_guess == str_real:
            N_correct_seq += 1

        if str_guess == str_query:
            N_correct_full += 1

        if len(tokens) >= 3:
            N_seq_long += 1
            if str_guess == str_real:
                N_correct_seq_long += 1

    print(f"Results for run {run_index}")
    print(f"Correct guess (token): {N_correct}/{len(assignments)} (%.2f%%)" % (N_correct/len(assignments)*100))
    print(f"Correct guess (token sequence): {N_correct_seq}/{len(string_freq)} (%.2f%%)" % (N_correct_seq/len(string_freq)*100))
    print(f"Correct guess (full query): {N_correct_full}/{len(string_freq)} (%.2f%%)" % (N_correct_full/len(string_freq)*100))
    print(f"Coverage (over all tokens): {N_coverage}/{N_coverage_total} (%.2f%%)" % (N_coverage/N_coverage_total*100))


    file_out = open(file_name_output + f'report_{N_doc}_{N_qry}_{N_index}_{run_index}.txt', 'w')
    file_out.write(f"{N_correct}, {len(assignments)}\n")
    file_out.write(f"{N_correct_seq}, {len(string_freq)}\n")
    file_out.write(f"{N_correct_full}, {len(string_freq)}\n")
    file_out.write(f"{N_coverage}, {N_coverage_total}\n")
    file_out.write(f"{N_correct_seq_long}, {N_seq_long}\n")


    tokens_set1 = set()
    tokens_set1.update(string_freq.keys())
    tokens_set2 = set()

    ctr = 0

    str_idx = 0
    while len(tokens_set1) > 0:
        for tokens in tokens_set1:
            if len(tokens) <= str_idx:
                continue
            leakage_id = leakage_tokens_to_id_map[tokens]
            str_query = leakage_dict[leakage_id]['query_str']

            if assignments[tokens[str_idx]] == str_query[str_idx]:
                tokens_set2.add(tokens)

        file_out.write(f"{str_idx}, {len(tokens_set2)}, {len(tokens_set1)}\n")

        tokens_set1 = set()
        tokens_set1.update(tokens_set2)
        tokens_set2 = set()

        str_idx += 1

    
    file_out.close()

    '''
    file_out = open(file_name_output + f'assignment_{N_doc}_{N_qry}_{N_index}_{run_index}.json', 'w')
    json.dump(assignments, file_out)
    file_out.close()

    file_out = open(file_name_output + f'scores_{N_doc}_{N_qry}_{N_index}_{run_index}.json', 'w')
    json.dump(scores, file_out)
    file_out.close()
    '''
