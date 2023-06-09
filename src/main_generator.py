import os
import numpy as np
import pandas as pd

### CONFIGURATION PARAMETERS ###

DATA_PATH = "data"  # name of the result path

CLUSTERS_NUM = 4    # Max value must be = SIGNIFICANT_NUM^2
INSTANCES = 10     # INSTANCES per cluster

SIGNIFICANT_NUM = 3  # Number of significant columns. Please, pay attention to CLUSTER_NUM
DUMMY_NUM = 3       # Number of dummy columns

STANDARD_DEV = 0.05  # Standard Deviation for the Normal Distribution of data

ADD_CLUSTERING_LABEL = True

#################################

FEATURES = SIGNIFICANT_NUM + DUMMY_NUM
ROWS = INSTANCES * CLUSTERS_NUM


def generate_random_numbers(clusters_num=CLUSTERS_NUM):
    """Generate a list of random number without repetition. The list has the same size as the number of clusters given."""
    l_random_values = []
    numbers = set()
    i = 0
    while i < clusters_num:
        n = get_random_number(min=0, max=clusters_num)
        if n not in numbers:
            numbers.add(n)
            l_random_values.append(n)
            i += 1
    return l_random_values


def binarize_numbers(list_numbers: list):
    """Returns a list of binarized number from the list of numbers given.   """
    list_bin = []
    for num in list_numbers:
        binarized = convert_to_binary(num)
        list_bin.append(binarized)
    return list_bin


def define_clusters(list_bin):
    """From a list of binary numbers, it returns a list of values depending on the zero or 1 from the bin number.
    Each value of the list_bin will define a cluster configuration.
    """
    res = []
    for par in list_bin:
        l = []
        for x in par:
            l.append(get_value(x))
        res.append(l)
    return res


def generate_columns(mean_features, instances=INSTANCES):
    """
    It receives a list of list with the values of the means for creating the clusters. It return a numpy array 
    with SIGNIFICANT_NUM + DUMMY_NUM columns.
    """
    j = 0
    clusters_list = []
    while j < SIGNIFICANT_NUM:
        x_list = []
        for i, _ in enumerate(mean_features):
            values = np.random.normal(
                mean_features[i][j], STANDARD_DEV, instances)
            x_list.append(values)
            #print(f'x_list: {x_list}')
        j += 1
        numpy_list = np.concatenate(x_list)  # Concatenate the cluster
        clusters_list.append(numpy_list)

    dummy_list = []
    for c in range(0, DUMMY_NUM):        
        a = 0
        b = 1#CLUSTERS_NUM * 2
        # random_dummy_array = np.random.normal(a, b, ROWS)
        rng = np.random.default_rng()
        random_dummy_array = (b - a) * rng.random(size=ROWS) + a
        dummy_list.append(random_dummy_array)

    res = clusters_list + dummy_list
    numpy_res = np.vstack(res)
    numpy_res = np.transpose(numpy_res)

    return numpy_res


def get_value(number: str):
    """Returns a 0.25 if the given value is a '0', else 0.75 """
    return 0.25 if number == '0' else 0.75


def convert_to_binary(number: int, features_number=SIGNIFICANT_NUM):
    """Returns the given number in binary with a padding of feature_number"""
    binary = format(number, f'0{features_number}b')
    return binary


def get_random_number(min: int, max: int):
    """Returns a random number between the min and max given values."""
    rng = np.random.default_rng()
    return int((max - min) * rng.random() + min)


def generate_dataset():
    """It calls the functions in order to create the dataset."""
    print('Generating dataset...')
    random_array = generate_random_numbers(CLUSTERS_NUM)
    bin_array = binarize_numbers(random_array)
    mean_features = define_clusters(bin_array)
    print('Dataset generated succesfully!\n')

    return generate_columns(mean_features)

def get_column_names():
    return [f's{n}' for n in range(SIGNIFICANT_NUM)] + [f'd{d}' for d in range(DUMMY_NUM)]

def add_clustering_label(data):
    """It adds the clustering label to the data"""
    data['n'] = np.arange(data.shape[0])
    data['cluster'] = data['n'].apply(get_cluster_number)
    data.drop(['n'], axis=1, inplace=True)
    return data

def get_cluster_number(n):
    return n//INSTANCES

def save_dataset(data):
    """It saves the pandas Dataframe into a file with the following name: k2_100i_s2-d8-sd0.05.csv
    where: 
    -k is number of clusters.
    -i is the number of instances of each cluster
    -s is the number of significant columns
    -d is the number of dummy columns
    -sd is the value of the standard deviation of the normal distribution
    """
    print(f'Saving dataset into {DATA_PATH} folder...')
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    # filename => k2_100i_s2-d8-sd0.05.csv
    filename = f'k{CLUSTERS_NUM}_{INSTANCES}i_s{SIGNIFICANT_NUM}-d{DUMMY_NUM}-sd{STANDARD_DEV}.csv'
    data.to_csv(f'{DATA_PATH}\\{filename}', sep=",", index=False)
    print(f'File "{filename}" saved succesfully!')


def main():
    """Main function"""
    data = generate_dataset()

    columns = get_column_names()
    data = pd.DataFrame(data, columns = columns)


    if ADD_CLUSTERING_LABEL:
        data = add_clustering_label(data)

    save_dataset(data)


if __name__ == "__main__":
    main()
