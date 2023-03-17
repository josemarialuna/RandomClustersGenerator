import os
import numpy as np

DATA_PATH = "data"

CLUSTER_NUM = 2
INSTANCES = 10     # INSTANCES per cluster

CLUSTERS_COL_NUM = 2
DUMMY_COL_NUM = 8

ROWS = INSTANCES * CLUSTER_NUM
COLS = CLUSTERS_COL_NUM+DUMMY_COL_NUM

#res = np.empty((INSTANCES, COLS), float)
clusters_list = []

for c in range(0, CLUSTERS_COL_NUM):
    x_list = []

    for k in range(0, CLUSTER_NUM):
        random_norm_column = np.random.normal(2*k, 0.1, INSTANCES)
        x_list.append(random_norm_column)

    numpy_list = np.concatenate(x_list)

    clusters_list.append(numpy_list)


dummy_list = []
for c in range(0, DUMMY_COL_NUM):
    rng = np.random.default_rng()
    a = 0
    b = CLUSTER_NUM*2
    random_dummy_array = (b - a) * rng.random(size=ROWS) + a
    dummy_list.append(random_dummy_array)

res = clusters_list + dummy_list
numpy_res = np.vstack(res)
numpy_res = np.transpose(numpy_res)

print(numpy_res)
print(numpy_res.shape)

if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

# filename => k2_100i_c2-d8.csv
filename = f'f{CLUSTER_NUM}_{INSTANCES}i_c{CLUSTERS_COL_NUM}-d{DUMMY_COL_NUM}.csv'
np.savetxt(f'{DATA_PATH}\\{filename}', numpy_res, delimiter=",")
