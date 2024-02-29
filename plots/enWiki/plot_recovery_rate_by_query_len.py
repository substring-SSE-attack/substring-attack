import os
import matplotlib.pyplot as plt



def parse_files(folder):
    results = {}
    for file_name in os.listdir(folder):
        file_name_segments = file_name.split('_')
        if file_name_segments[0] != "report":
            continue
        N_doc   = int(file_name_segments[1])
        N_query = int(file_name_segments[2])
        index   = int(file_name_segments[3])

        if N_doc != 100000:
            continue
        
        if N_query != 10000:
            continue
        
        category = index // 5
        if category not in results:
            results[category] = {'token_unique': [0,0],
                                 'token_rep':    [0,0],
                                 'token_seq':    [0,0],
                                 'query_full':   [0,0],
                                 'long_rec':     [0,0],}

        file_input = open(folder+file_name, 'r')
        line = file_input.readline().split(',')
        results[category]['token_unique'][0] += int(line[0])
        results[category]['token_unique'][1] += int(line[1])

        line = file_input.readline().split(',')
        results[category]['token_seq'][0] += int(line[0])
        results[category]['token_seq'][1] += int(line[1])

        line = file_input.readline().split(',')
        results[category]['query_full'][0] += int(line[0])
        results[category]['query_full'][1] += int(line[1])

        line = file_input.readline().split(',')
        results[category]['token_rep'][0] += int(line[0])
        results[category]['token_rep'][1] += int(line[1])

        line = file_input.readline().split(',')
        results[category]['long_rec'][0] += int(line[0])
        results[category]['long_rec'][1] += int(line[1])
        
        file_input.close()
        

    return results


folder = '../../results/enWiki/'
results = parse_files(folder)

query_lens = {0: "3-11",
              1: "1-11",
              2: "3-7",
              3: "3-9",
              4: "3-13",
              }

for category in [1,2,3,0,4]:
    print(category, end="\t")
    print(query_lens[category], end="\t")
    print("%.1f%%" % (results[category]['token_unique'][0] / results[category]['token_unique'][1] * 100), end="\t")
    print("%.1f%%" % (results[category]['token_rep'][0] / results[category]['token_rep'][1] * 100), end="\t")
    print("%.1f%%" % (results[category]['token_seq'][0] / results[category]['token_seq'][1] * 100), end="\t")
    print("%.1f%%" % (results[category]['query_full'][0] / results[category]['query_full'][1] * 100), end="\t")
    print("%.1f%%" % (results[category]['long_rec'][0] / results[category]['long_rec'][1] * 100))


