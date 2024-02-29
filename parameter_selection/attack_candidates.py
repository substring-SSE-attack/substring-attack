import time
import numpy as np

BUCKET_SIZE = 100

# Find candidates for each token at level 0
def find_token_candidates_level0(candidates_token_seq, leakage_level_dict, string_freq, id_to_leakage_tokens_map, auxiliary_freq, auxiliary_freq_lookup, sigma=6):
    count = 0
    for leakage_id in leakage_level_dict:
        tokens = id_to_leakage_tokens_map[leakage_id]

        if count % (len(leakage_level_dict) // 5) == 0:
            print(f"Identifying tokens at level 0: {count} / {len(leakage_level_dict)}")
        count += 1

        deviation = np.sqrt(string_freq[tokens])
        bound_lower = string_freq[tokens]-sigma*deviation
        bound_upper = string_freq[tokens]+sigma*deviation

        bound_lower_bucket = max(0, int(bound_lower // BUCKET_SIZE * BUCKET_SIZE))
        bound_upper_bucket = int(bound_upper // BUCKET_SIZE * BUCKET_SIZE + BUCKET_SIZE)

        # find string candidates for the token sequence
        # restrictions: 1. Length. 2. Same prefix as token_common_prefix. 3. Frequency.
        string_candidates = []
        for bucket_id in range(bound_lower_bucket, bound_upper_bucket, BUCKET_SIZE):
            if bucket_id not in auxiliary_freq_lookup:
                continue

            if len(tokens) not in auxiliary_freq_lookup[bucket_id]:
                continue
            
            for string_real in auxiliary_freq_lookup[bucket_id][len(tokens)]:
                if auxiliary_freq[string_real] >= bound_lower and auxiliary_freq[string_real] <= bound_upper:
                    string_candidates += [string_real]
        
        candidates_token_seq[tokens] = string_candidates

    return candidates_token_seq



# Find candidates for each token at a higher level
def find_token_candidates_level1(candidates_token_seq, leakage_level_dict, leakage_tree,string_freq, id_to_leakage_tokens_map, auxiliary_freq, auxiliary_freq_lookup, sigma=6):
    for leakage_id in leakage_level_dict:
        tokens = id_to_leakage_tokens_map[leakage_id]
        tokens_parent = id_to_leakage_tokens_map[leakage_tree[leakage_id]['parent']]
        candidates_parent = candidates_token_seq[tokens_parent]
        if len(candidates_parent) == 0:
            candidates_token_seq[tokens] = set()
            continue
        
        len_parent = len(candidates_parent[0])
        candidates_parent = set(candidates_parent)

        deviation = np.sqrt(string_freq[tokens])
        bound_lower = string_freq[tokens]-sigma*deviation
        bound_upper = string_freq[tokens]+sigma*deviation


        bound_lower_bucket = max(0, int(bound_lower // BUCKET_SIZE * BUCKET_SIZE))
        bound_upper_bucket = int(bound_upper // BUCKET_SIZE * BUCKET_SIZE + BUCKET_SIZE)

        string_candidates = []
        for bucket_id in range(bound_lower_bucket, bound_upper_bucket, BUCKET_SIZE):
            if bucket_id not in auxiliary_freq_lookup:
                continue

            if len(tokens) not in auxiliary_freq_lookup[bucket_id]:
                continue
            
            for string_real in auxiliary_freq_lookup[bucket_id][len(tokens)]:
                if string_real[:len_parent] in candidates_parent and auxiliary_freq[string_real] >= bound_lower and auxiliary_freq[string_real] <= bound_upper:
                    string_candidates += [string_real]
        
        candidates_token_seq[tokens] = string_candidates         

    return candidates_token_seq


def compute_candidates_token_score(candidates_token_score, candidates_token_seq, leakage_level_dict, id_to_leakage_tokens_map, char_set):
    # reset scores for the tokens that are touched
    for leakage_id in leakage_level_dict:
        tokens = id_to_leakage_tokens_map[leakage_id]
        for token in tokens:
            for char in char_set:
                candidates_token_score[token][char] = 0
            candidates_token_score[token]['count'] = 0


    for leakage_id in leakage_level_dict:
        tokens = id_to_leakage_tokens_map[leakage_id]

        # initialise the candidate set for the token string
        candidates_local = {}
        for token in tokens:
            candidates_local[token] = set()

        # for each string candidate, add the character in position i to the candidate set of the token in position i
        for string_candidate in candidates_token_seq[tokens]:
            for token, char in zip(tokens, string_candidate):
                candidates_local[token].add(char)
        
        # for each string candidate, add the character in position i to the candidate set of the token in position i
        for string_candidate in candidates_token_seq[tokens]:
            for token, char in zip(tokens, string_candidate):
                candidates_local[token].add(char)
        
        # update the candidates token score
        for token in tokens:
            for char in candidates_token_score[token]:
                if char in candidates_local[token]:
                    candidates_token_score[token][char] += 1
                elif len(char) == 1:
                    candidates_token_score[token][char] -= 1
            candidates_token_score[token]['count'] += 1

    return candidates_token_score



def refine_candidates_token(candidates_token, candidates_token_score, N_filter=5):
    for token in candidates_token:
        if candidates_token_score[token]['count'] == 0:
            continue
        
        # find the best N_filter candidates
        candidates_sorted = sorted(candidates_token_score[token].keys(), key=lambda x: candidates_token_score[token][x], reverse=True)
        candidates_new = set()
        for cand in candidates_sorted:
            if cand != 'count' and candidates_token_score[token][cand] == candidates_token_score[token]['count']:
                candidates_new.add(cand)

        if len(candidates_new) < N_filter:
            ctr = 0
            while ctr < len(candidates_sorted) and len(candidates_new) < N_filter:
                if candidates_sorted[ctr] != 'count' and candidates_token_score[token][candidates_sorted[ctr]] > 0:
                    candidates_new.add(candidates_sorted[ctr])
                ctr += 1

        candidates_token[token] = set()
        for cand in candidates_new:
            if candidates_token_score[token][cand] > 0:
                candidates_token[token].add(cand)

    return candidates_token

# remove inconsistent candidates based on candidates_token (and more later)
def remove_inconsistent_token_seq(candidates_token, candidates_token_seq, leakage_level_dict, id_to_leakage_tokens_map):
    count = 0
    for leakage_id in leakage_level_dict:
        tokens = id_to_leakage_tokens_map[leakage_id]
        for candidate in candidates_token_seq[tokens]:
            flag_bad_cand = False
            for token, cand_char in zip(tokens, candidate):
                if cand_char not in candidates_token[token]:
                    flag_bad_cand = True
                    break
            if flag_bad_cand == True:
                candidates_token_seq[tokens].remove(candidate)
                count += 1

    return candidates_token_seq, count


# Find candidates for each token at level 0
def fill_candidates(candidates_token_seq, string_freq, auxiliary_freq, auxiliary_freq_lookup, sigma=6):
    count = 0
    for tokens in candidates_token_seq:
        if len(candidates_token_seq[tokens]) > 0:
            continue

        width = sigma
        while len(candidates_token_seq[tokens]) == 0:
            deviation = np.sqrt(string_freq[tokens])
            bound_lower = string_freq[tokens] - width*deviation
            bound_upper = string_freq[tokens] + width*deviation

            bound_lower_bucket = max(0, int(bound_lower // BUCKET_SIZE * BUCKET_SIZE))
            bound_upper_bucket = int(bound_upper // BUCKET_SIZE * BUCKET_SIZE + BUCKET_SIZE)

            # find string candidates for the token sequence
            # restrictions: 1. Length. 2. Same prefix as token_common_prefix. 3. Frequency.
            string_candidates = []
            for bucket_id in range(bound_lower_bucket, bound_upper_bucket, BUCKET_SIZE):
                if bucket_id not in auxiliary_freq_lookup:
                    continue

                if len(tokens) not in auxiliary_freq_lookup[bucket_id]:
                    continue
                
                for string_real in auxiliary_freq_lookup[bucket_id][len(tokens)]:
                    if auxiliary_freq[string_real] >= bound_lower and auxiliary_freq[string_real] <= bound_upper:
                        string_candidates += [string_real]
            
            candidates_token_seq[tokens] = string_candidates

            width += 1

    return candidates_token_seq




# Find candidates for each token based on string frequencies
def find_token_candidates(char_equality_group, leakage_tree, leakage_level, string_freq, id_to_leakage_tokens_map, auxiliary_freq, char_set, sigma=6, N_filter=5):
    candidates_token = {}
    candidates_token_score = {}
    candidates_token_seq = {}

    # initialise candidates token
    for token in char_equality_group:
        candidates_token[token] = char_set

    # initialise the scores of each token
    # score here tracks how likely a character corresponds to a token
    for token in char_equality_group:
        candidates_token_score[token] = {}
        for char in char_set:
            candidates_token_score[token][char] = 0
        candidates_token_score[token]['count'] = 0


    # group auxiliary frequency by frequency for quick lookup
    auxiliary_freq_lookup = {}
    for tokens in auxiliary_freq:
        bucket = auxiliary_freq[tokens] // BUCKET_SIZE * BUCKET_SIZE
        if bucket not in auxiliary_freq_lookup:
            auxiliary_freq_lookup[bucket] = {}
        if len(tokens) not in auxiliary_freq_lookup[bucket]:
            auxiliary_freq_lookup[bucket][len(tokens)] = []
        auxiliary_freq_lookup[bucket][len(tokens)].append(tokens)
    

    # set up the token candidates at the lowest level
    level_min = min(leakage_level.keys())
    time_start = time.time()
    candidates_token_seq = find_token_candidates_level0(candidates_token_seq, leakage_level[level_min], string_freq, id_to_leakage_tokens_map, auxiliary_freq, auxiliary_freq_lookup, sigma=sigma)
    N_inconsistent = 1
    while N_inconsistent != 0:
        time_refine = time.time()
        candidates_token_score = compute_candidates_token_score(candidates_token_score, candidates_token_seq, leakage_level[level_min], id_to_leakage_tokens_map, char_set)
        candidates_token = refine_candidates_token(candidates_token, candidates_token_score, N_filter=N_filter)
        candidates_token_seq, N_inconsistent = remove_inconsistent_token_seq(candidates_token, candidates_token_seq, leakage_level[level_min], id_to_leakage_tokens_map)
        print(f"Inconsistent candidates removed: {N_inconsistent}, time taken: %.2f seconds" % (time.time() - time_refine))
    print("Lvel 0 tokens identified: %.2f seconds" % (time.time() - time_start))


    # iterate through other levels of the leakage tree
    for level in sorted(leakage_level.keys()):
        if level == level_min:
            continue

        time_start = time.time()
        candidates_token_seq = find_token_candidates_level1(candidates_token_seq, leakage_level[level], leakage_tree, string_freq, id_to_leakage_tokens_map, auxiliary_freq, auxiliary_freq_lookup, sigma=sigma)
        N_inconsistent = 1
        while N_inconsistent != 0:
            time_refine = time.time()
            candidates_token_score = compute_candidates_token_score(candidates_token_score, candidates_token_seq, leakage_level[level], id_to_leakage_tokens_map, char_set)
            candidates_token = refine_candidates_token(candidates_token, candidates_token_score, N_filter=N_filter)
            candidates_token_seq, N_inconsistent = remove_inconsistent_token_seq(candidates_token, candidates_token_seq, leakage_level[level], id_to_leakage_tokens_map)
            print(f"Inconsistent candidates removed: {N_inconsistent}, time taken: %.2f seconds" % (time.time() - time_refine))
        print(f"Level {level} cleaned: %.2f seconds" % (time.time() - time_start))
    
    # fill the tokens with no candidate with some placeholders
    candidates_token_seq = fill_candidates(candidates_token_seq, string_freq, auxiliary_freq, auxiliary_freq_lookup)

    return candidates_token, candidates_token_seq
