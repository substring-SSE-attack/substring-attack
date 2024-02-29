import json
import os


data_all = []
parent_folder = "./text/"

for folder in os.listdir(parent_folder):
    for file_name in os.listdir(parent_folder + folder):
        file_input = open(parent_folder + folder + "/" + file_name, "r", encoding="utf-8")
        for line in file_input.readlines():
            data = json.loads(line)
            if len(data["text"]) > 50:
                data_all += [data]
        file_input.close()


file_output = open("./output/enWiki.json", "w", encoding="utf-8")
json.dump(data_all, file_output)
file_output.close()
