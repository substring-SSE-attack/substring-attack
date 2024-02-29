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

        if N_doc != 1:
            continue

        if index >= 5:
            continue
        
        if N_query not in results:
            results[N_query] = {'token_unique': [0,0],
                                'token_rep':    [0,0],
                                'token_seq':    [0,0],
                                'query_full':   [0,0],}

        file_input = open(folder+file_name, 'r')
        line = file_input.readline().split(',')
        results[N_query]['token_unique'][0] += int(line[0])
        results[N_query]['token_unique'][1] += int(line[1])

        line = file_input.readline().split(',')
        results[N_query]['token_seq'][0] += int(line[0])
        results[N_query]['token_seq'][1] += int(line[1])

        line = file_input.readline().split(',')
        results[N_query]['query_full'][0] += int(line[0])
        results[N_query]['query_full'][1] += int(line[1])

        line = file_input.readline().split(',')
        results[N_query]['token_rep'][0] += int(line[0])
        results[N_query]['token_rep'][1] += int(line[1])
        
        file_input.close()
        

    return results

def plot_results(results):
    xs = sorted(results.keys())

    plt.rc('axes', titlesize=14)    
    plt.rc('axes', labelsize=14)
    plt.rc('xtick', labelsize=14)    
    plt.rc('ytick', labelsize=14)


    token_recov =       [results[x]['token_unique'][0] / results[x]['token_unique'][1] *100 for x in xs]
    token_seq_recov =   [results[x]['token_seq'][0] / results[x]['token_seq'][1] *100 for x in xs]
    query_recov =       [results[x]['query_full'][0] / results[x]['query_full'][1] *100 for x in xs]
    token_rep_recov =   [results[x]['token_rep'][0] / results[x]['token_rep'][1] *100 for x in xs]

    plt.scatter(xs, token_recov,        color='black',  marker='o', label='Unique token')
    plt.scatter(xs, token_rep_recov,    color='black',  marker='*', label='Token with repetition')
    plt.scatter(xs, token_seq_recov,    color='black',  marker='x', label='Initial path')
    plt.scatter(xs, query_recov,        color='black',  marker='v', label='Query')

    plt.xlabel('#queries')
    plt.ylabel('Recovery rate (%)')

    plt.ylim([20,80])
    plt.legend(fontsize=14)
    
    plt.show()

folder = '../../results/genome/'
results = parse_files(folder)
plot_results(results)


