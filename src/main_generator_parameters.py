import csv
import os
from collections import namedtuple
import numpy as np
import pandas as pd

### CONFIGURATION PARAMETERS ###
DATA_PATH = "data"  # name of the result path
INSTANCES = 100
ADD_CLUSTERING_LABEL = True
#################################

Config = namedtuple('Config', 'name, clusters_num, instances, significant_num, dummy_num, standard_dev')

def get_config_vars():
    config = list()
    with open('config\\datasets_values.csv') as csvfile:
        reader = csv.reader(csvfile, delimiter=';') 
        next(reader)       
        for clusters_num, significant_num, dummy_num, standard_dev in reader:
            #name => k2_100i_s2-d8-sd0.05
            name = f'k{clusters_num}_{INSTANCES}i_s{significant_num}-d{dummy_num}-sd{standard_dev}'      
            config.append(Config(name, int(clusters_num), INSTANCES, int(significant_num), int(dummy_num), float(standard_dev)))
    return config



def generate_random_numbers(clusters_num):
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


def binarize_numbers(list_numbers: list, significant_num):
    """Returns a list of binarized number from the list of numbers given.   """
    list_bin = []
    for num in list_numbers:
        binarized = convert_to_binary(num, significant_num)
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


def generate_columns(mean_features, config):
    """
    It receives a list of list with the values of the means for creating the clusters. It return a numpy array 
    with SIGNIFICANT_NUM + DUMMY_NUM columns.
    """
    j = 0
    clusters_list = []
    while j < config.significant_num:
        x_list = []
        for i, _ in enumerate(mean_features):            
            values = np.random.normal(mean_features[i][j], config.standard_dev, config.instances)
            x_list.append(values)
            #print(f'x_list: {x_list}')
        j += 1
        numpy_list = np.concatenate(x_list)  # Concatenate the cluster
        clusters_list.append(numpy_list)

    dummy_list = []
    for c in range(0, config.dummy_num):        
        a = 0
        b = 1#CLUSTERS_NUM * 2
        # random_dummy_array = np.random.normal(a, b, ROWS)
        rng = np.random.default_rng()
        random_dummy_array = (b - a) * rng.random(size=config.clusters_num*config.instances) + a
        dummy_list.append(random_dummy_array)

    res = clusters_list + dummy_list
    numpy_res = np.vstack(res)
    numpy_res = np.transpose(numpy_res)

    return numpy_res


def get_value(number: str):
    """Returns a 0.25 if the given value is a '0', else 0.75 """
    return 0.25 if number == '0' else 0.75


def convert_to_binary(number: int, features_number):
    """Returns the given number in binary with a padding of feature_number"""
    binary = format(number, f'0{features_number}b')
    return binary


def get_random_number(min: int, max: int):
    """Returns a random number between the min and max given values."""
    rng = np.random.default_rng()
    return int((max - min) * rng.random() + min)


def generate_dataset(config):
    """It calls the functions in order to create the dataset."""
    print('Generating dataset...')
    random_array = generate_random_numbers(config.clusters_num)
    bin_array = binarize_numbers(random_array, config.significant_num)
    mean_features = define_clusters(bin_array)
    print('Dataset generated succesfully!\n')

    return generate_columns(mean_features, config)

def get_column_names(config):
    return [f's{n}' for n in range(config.significant_num)] + [f'd{d}' for d in range(config.dummy_num)]

def add_clustering_label(data):
    """It adds the clustering label to the data"""
    data['n'] = np.arange(data.shape[0])
    data['cluster'] = data['n'].apply(get_cluster_number)
    data.drop(['n'], axis=1, inplace=True)
    return data

def get_cluster_number(n):
    return n//INSTANCES


def save_dataset(data, config):
    """It saves the numpy array into a file with the following name: k2_100i_s2-d8-sd0.05.csv
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
    filename = f'{config.name}.csv'
    data.to_csv(f'{DATA_PATH}\\{filename}', sep=",", index=False)
    print(f'File "{filename}" saved succesfully!')


def main():
    """Main function"""

    config = get_config_vars()
    for c in config:
        print(c)
        data = generate_dataset(c)

        columns = get_column_names(c)
        data = pd.DataFrame(data, columns = columns)

        if ADD_CLUSTERING_LABEL:
            data = add_clustering_label(data)

        save_dataset(data, c)


if __name__ == "__main__":
    main()
