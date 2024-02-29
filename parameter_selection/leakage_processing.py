import json
import pickle

            
def extract_prefix_equality(leakage_dict):
    # find all characters that are equal by comparing query responses with shared initial paths
    prefix_equality_dict = {}

    for leakage_id1 in leakage_dict:
        if leakage_id1 % (len(leakage_dict) // 10) == 0:
            print(f"Extracting prefix equality: {leakage_id1} / {len(leakage_dict)}")
        
        if 'str_idx' not in leakage_dict[leakage_id1]:
            continue
        
        prefix_equality_dict[leakage_id1] = {}
        
        for leakage_id2 in leakage_dict:
            if 'str_idx' not in leakage_dict[leakage_id2]:
                continue
            if leakage_id1 <= leakage_id2:
                continue

            if len(leakage_dict[leakage_id1]['prefix']) == 0 and len(leakage_dict[leakage_id2]['prefix']) == 0:
                continue


            # case 1: one initial path is a sub-initial path of the other initial path
            if leakage_id1 in leakage_dict[leakage_id2]['prefix']:
                common_prefix_len = leakage_dict[leakage_id1]['str_len']

                # add the prefix length info to prefix_equality_dict
                prefix_equality_dict[leakage_id1][leakage_id2] = common_prefix_len

                if leakage_id2 not in prefix_equality_dict:
                    prefix_equality_dict[leakage_id2] = {}
                prefix_equality_dict[leakage_id2][leakage_id1] = common_prefix_len
                

            elif leakage_id2 in leakage_dict[leakage_id1]['prefix']:
                common_prefix_len = leakage_dict[leakage_id2]['str_len']
                
                # add the prefix length info to prefix_equality_dict
                prefix_equality_dict[leakage_id1][leakage_id2] = common_prefix_len

                if leakage_id2 not in prefix_equality_dict:
                    prefix_equality_dict[leakage_id2] = {}
                prefix_equality_dict[leakage_id2][leakage_id1] = common_prefix_len



            # case 2: both initial paths have prefix, no initial path is a sub initial path of the other initial path
            elif len(leakage_dict[leakage_id1]['prefix']) > 0 and len(leakage_dict[leakage_id2]['prefix']) > 0:
                # find the length of the common prefix in terms of edges
                common_edge_len = 0
                while leakage_dict[leakage_id1]['prefix'][common_edge_len] == leakage_dict[leakage_id2]['prefix'][common_edge_len]:
                    common_edge_len += 1
                    if common_edge_len >= len(leakage_dict[leakage_id1]['prefix']) or common_edge_len >= len(leakage_dict[leakage_id2]['prefix']):
                        break

                if common_edge_len > 0:
                    # find the length of the common prefix in terms of characters
                    common_prefix_len = 1
                    if common_edge_len > 1:
                        common_prefix_len = leakage_dict[leakage_dict[leakage_id1]['prefix'][common_edge_len-1]]['str_len']

                    # add the prefix length info to prefix_equality_dict
                    prefix_equality_dict[leakage_id1][leakage_id2] = common_prefix_len

                    if leakage_id2 not in prefix_equality_dict:
                        prefix_equality_dict[leakage_id2] = {}
                    prefix_equality_dict[leakage_id2][leakage_id1] = common_prefix_len

            
    return prefix_equality_dict


def extract_character_equality(leakage_dict, prefix_equality_dict):
    char_equality_list = []

    # get character level equality
    for leakage_id1 in leakage_dict:
        for leakage_id2 in leakage_dict:
            if leakage_id1 <= leakage_id2:
                continue
            if leakage_id1 in prefix_equality_dict and leakage_id2 in prefix_equality_dict[leakage_id1]:
                common_prefix_len = prefix_equality_dict[leakage_id1][leakage_id2]
                for ii in range(common_prefix_len):
                    char_equality_list.append(((leakage_id1, ii), (leakage_id2, ii)))
    
    
    # build character equality groups
    char_equality_group_ctr = 0
    char_equality_group = {}
    char_equality_inv   = {}

    for idx1, idx2 in char_equality_list:
        if idx1 not in char_equality_inv and idx2 not in char_equality_inv:
            char_equality_inv[idx1] = char_equality_group_ctr
            char_equality_inv[idx2] = char_equality_group_ctr
            char_equality_group_ctr += 1
        elif idx1 not in char_equality_inv:
            char_equality_inv[idx1] = char_equality_inv[idx2]
        elif idx2 not in char_equality_inv:
            char_equality_inv[idx2] = char_equality_inv[idx1]

        if char_equality_inv[idx1] not in char_equality_group:
            char_equality_group[char_equality_inv[idx1]] = set()
        char_equality_group[char_equality_inv[idx1]].add(idx1)
        char_equality_group[char_equality_inv[idx1]].add(idx2)


    # adding isolated characters
    for leakage_id in leakage_dict:
        str_len = leakage_dict[leakage_id]['str_len']
            
        for ctr in range(str_len):
            key = (leakage_id, ctr)
            if key not in char_equality_inv:
                char_equality_inv[key] = char_equality_group_ctr
                char_equality_group[char_equality_group_ctr] = set([key])
                char_equality_group_ctr += 1
            

    return char_equality_group, char_equality_inv





def extract_string_frequency(leakage_dict, char_equality_inv):
    string_freq = {}
    leakage_tokens_to_id_map = {}
    id_to_leakage_tokens_map = {}
    
    for leakage_id in leakage_dict:
        if 'leafCount' not in  leakage_dict[leakage_id]:
            continue
        
        str_len = leakage_dict[leakage_id]['str_len']

        char_seq = []
        for ctr in range(str_len):
            char_seq += [char_equality_inv[(leakage_id, ctr)]]

        string_freq[tuple(char_seq)] = leakage_dict[leakage_id]['leafCount']

        leakage_tokens_to_id_map[tuple(char_seq)] = leakage_id
        id_to_leakage_tokens_map[leakage_id] = tuple(char_seq)

    return string_freq, leakage_tokens_to_id_map, id_to_leakage_tokens_map



def extract_leakage_tree(leakage_dict, id_to_leakage_tokens_map):
    leakage_tree = {}
    leakage_level = {}
    for leakage_id1 in leakage_dict:
        prefix = leakage_dict[leakage_id1]['prefix']
        leakage_id_last = -1
        level = 0
        for leakage_id2 in prefix:
            if leakage_id2 in leakage_dict and 'leafCount' in leakage_dict[leakage_id2]:
                leakage_id_last = leakage_id2
                level += 1

        if leakage_id_last != -1:
            if leakage_id1 not in leakage_tree:
                leakage_tree[leakage_id1] = {
                    'parent':   None,
                    'children': set()}
            if leakage_id_last not in leakage_tree:
                leakage_tree[leakage_id_last] = {
                    'parent':   None,
                    'children': set()}

            # add parent/children to the tree
            leakage_tree[leakage_id1]['parent'] = leakage_id_last
            leakage_tree[leakage_id_last]['children'].add(leakage_id1)

        if 'leafCount' in leakage_dict[leakage_id1]:
            if level not in leakage_level:
                leakage_level[level] = []
            leakage_level[level] += [leakage_id1]

    for level in leakage_level:
        leakage_level[level] = sorted(leakage_level[level], key=lambda x: leakage_dict[x]['leafCount'], reverse=True)

    return leakage_tree, leakage_level
                
                

def extract_overlap_leakage(leakage_dict):
    overlap_leakage = {}

    for leakage_id in leakage_dict:
        if 'str_idx' not in leakage_dict[leakage_id]:
            continue
        overlap_leakage[leakage_id] = {}
    
    for leakage_id1 in leakage_dict:
        if 'str_idx' not in leakage_dict[leakage_id1]:
            continue
        
        for leakage_id2 in leakage_dict:
            if 'str_idx' not in leakage_dict[leakage_id2]:
                continue
            if leakage_id1 >= leakage_id2:
                continue

            idx1 = leakage_dict[leakage_id1]['str_idx']
            len1 = leakage_dict[leakage_id1]['str_len']
            idx2 = leakage_dict[leakage_id2]['str_idx']
            len2 = leakage_dict[leakage_id2]['str_len']

            if idx1[0] != idx2[0]:
                continue

            if idx1[1] < idx2[1]:
                if idx1[1] + len1 - 1 >= idx2[1] and idx1[1] + len1 - 1 < idx2[1] + len2 - 1:
                    overlap_len = idx1[1] + len1 - idx2[1]
                    overlap_leakage[leakage_id1][leakage_id2] = overlap_len
                    overlap_leakage[leakage_id2][leakage_id1] = overlap_len
            elif idx2[1] < idx1[1]:
                if idx2[1] + len2 - 1 >= idx1[1] and idx2[1] + len2 - 1 < idx1[1] + len1 - 1:
                    overlap_len = idx2[1] + len2 - idx1[1]
                    overlap_leakage[leakage_id1][leakage_id2] = overlap_len
                    overlap_leakage[leakage_id2][leakage_id1] = overlap_len

    return overlap_leakage

