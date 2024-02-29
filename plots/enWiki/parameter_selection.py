import os
import matplotlib.pyplot as plt
import numpy as np


def parse_files(folder):
    results = {}
    for file_name in os.listdir(folder):
        file_name_segments = file_name.split('_')
        if file_name_segments[0] != "report":
            continue
        N_doc   = int(file_name_segments[1])
        N_query = int(file_name_segments[2])
        sigma   = int(file_name_segments[3])
        threshold   = int(file_name_segments[4])

        
        if (sigma, threshold) not in results:
            results[(sigma, threshold)] = {'rs': [],
                                           'hit': []}


        file_input = open(folder+file_name, 'r')
        line = file_input.readline()
        results[(sigma, threshold)]['rs'] += [float(line)]

        line = file_input.readline().split(',')
        results[(sigma, threshold)]['hit'] += [int(line[0]) / int(line[1])]

        
        file_input.close()
        

    return results


folder = '../../results_parameters/enWiki/'
results = parse_files(folder)

for sigma, threshold in sorted(results.keys()):
    rs = np.mean(results[(sigma, threshold)]['rs'])
    hr = np.mean(results[(sigma, threshold)]['hit'])
    print(f"{sigma}\t{threshold}\t", end="")
    print("%.2f\t" % rs, end="")
    print("%.2f%%\t" % (hr*100))


