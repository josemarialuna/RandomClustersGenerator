k = [2, 4, 6, 10]
significativas = [2, 4, 6, 8, 10]
dummies = [2, 4, 6, 8, 10, 20]
desviaciones = [0.01, 0.05, 0.075, 0.1]
lines = list()

for i in k:
    for s in significativas:
        for d in dummies:
            for de in desviaciones:
                lines.append(f'{i};{s};{d};{de}')

with open('config/new_data.csv', 'w') as f:
    f.write('clusters_num;significant_num;dummy_num;standard_dev\n')
    for line in lines:
        f.write(f"{line}\n")
