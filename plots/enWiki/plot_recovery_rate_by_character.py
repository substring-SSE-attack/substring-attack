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
        if index >= 5:
            continue

        if N_query not in results:
            results[N_query] = {}

        file_input = open(folder+file_name, 'r')
        for ii in range(4):
            file_input.readline()

        for line in file_input.readlines()[:-1]:
            data = line.split(',')
            index = int(data[0])
            correct = int(data[1])
            total = int(data[2])

            if index not in results[N_query]:
                results[N_query][index] = [correct, total, 1]
            else:
                results[N_query][index][0] += correct
                results[N_query][index][1] += total
                results[N_query][index][2] += 1
        file_input.close()
        

    return results

def plot_results(results):
    xs = sorted(results.keys())


    token_recov =       [results[x][0] / results[x][2] for x in xs]
    token_total =       [results[x][1] / results[x][2] for x in xs]
    xs = [x+1 for x in xs]

    
    plt.bar(xs, token_total, fill=False, label='Total')
    plt.bar(xs, token_recov, fill=False, hatch='/', label='Recovered')


    plt.xlabel('Position')
    plt.ylabel('Counts')

    plt.legend()
    
    plt.show()

folder = '../../results/enWiki/'
results = parse_files(folder)
plot_results(results[10000])


