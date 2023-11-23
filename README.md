<a name="readme-top"></a>
# Random Clusters Generator
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

Generate datasets with defined clusters using a normal distribution. This specialized tool allows you to customize data creation, specifying the number of significant columns forming the clusters. Additionally, it provides the option to include dummy columns, adding variability and noise to your datasets.

## Key Features:

- **Defined Clusters:** Create datasets with clearly defined clusters, ideal for applying clustering algorithms.
- **Normal Distribution:** Utilize a normal distribution to generate data, providing realism and coherence in your datasets.
- **Significant Columns Configuration:** Customize the number of columns forming clusters, allowing you to adjust the complexity of your datasets.
- **Optional Dummy Columns:** Add dummy columns to introduce variability and noise in the data, providing a more realistic approach to real-world scenarios.


## Project Status

🚀 **In Development | Production Ready**

This project is in constant evolution to enhance and expand its functionalities. We welcome any community contributions to make it even more robust.
While the current version is ready for deployment in production environments, we are committed to continuous improvement and optimization of the code. Feel free to explore, use, and contribute to the project. Refer to the Contribution section for more details on how to get involved in development.
Your feedback and suggestions are valuable to us. Together, we can make this project even better!

# Project Structure

This project consists of three main files, each serving a specific purpose:

- **`main_generator.py`**: This file is responsible for generating datasets based on the parameters provided. It allows users to create customized datasets with defined clusters using a normal distribution. Users can specify the number of significant columns forming the clusters and choose to include additional dummy columns for added variability.
- **`main_generator_parameters.py`**: This file generates datasets based on parameters specified in a CSV file. Users can provide a CSV file containing configuration details, and the script will use this information to create datasets accordingly.
- **`add_dummy_columns.py`**: The purpose of this file is to add dummy columns to an existing CSV file. It takes a CSV file as input and appends additional columns with dummy data, introducing variability and noise to the dataset.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## How to use
### Configuration Parameters in `main_generator.py`
- **DATA_PATH:**  The name of the result path where generated datasets will be saved. Example: `DATA_PATH = "data"`
- **CLUSTERS_NUM:** The number of clusters to be generated. The maximum value must be equal to `SIGNIFICANT_NUM^2`. Example: `CLUSTERS_NUM = 4`
- **INSTANCES:**  The number of instances per cluster in the generated datasets. Example: `INSTANCES = 10`
- **SIGNIFICANT_NUM:** The number of significant columns forming the clusters. Pay attention to `CLUSTERS_NUM` as it must satisfy the condition `CLUSTERS_NUM = SIGNIFICANT_NUM^2`. Example: `SIGNIFICANT_NUM = 3`
- **DUMMY_NUM:**  The number of dummy columns to be included, adding variability and noise to the datasets. Example: `DUMMY_NUM = 3`
- **STANDARD_DEV:** The standard deviation for the Normal Distribution of data, influencing the spread of the generated values. Example: `STANDARD_DEV = 0.05`

### Configuration Parameters in `main_generator_parameters.py`
The `main_generator_parameters.py` script generates datasets based on configuration parameters specified in a CSV file. The CSV file should have the following columns:
- **clusters_num:** The number of clusters to be generated. It influences the structure of the datasets. Example: `clusters_num = 4`
- **significant_num:** The number of significant columns forming the clusters. It must satisfy the condition `clusters_num = significant_num^2`. Example: `significant_num = 3`
- **dummy_num:** Description: The number of dummy columns to be included, adding variability and noise to the datasets. Example: `dummy_num = 3`
- **standard_dev:** The standard deviation for the Normal Distribution of data, influencing the spread of the generated values. Example: `standard_dev = 0.05`

To use this script, create a CSV file with these columns and corresponding values, and then run the script by specifying the path to your CSV file.

#### Example CSV file:

```csv
clusters_num,significant_num,dummy_num,standard_dev
2,2,1,0.10
4,3,2,0.05
```
<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Resulting Datasets Examples

<p align="right">(<a href="#readme-top">back to top</a>)</p>

# Contribution
🎉 We welcome and encourage community contributions to enhance this project. Whether you want to report issues, propose new features, or submit improvements, your collaboration is valuable.

## How to Contribute
1. **Fork the Repository:**
   - Fork the repository to your GitHub account.

2. **Clone the Repository:**
   - Clone the forked repository to your local machine.
   ```bash
   git clone https://github.com/josemarialuna/RandomClustersGenerator.git
   cd RandomClustersGenerator

<p align="right">(<a href="#readme-top">back to top</a>)</p>

# License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

<p align="right">(<a href="#readme-top">back to top</a>)</p>

# Contact 

* **José María Luna-Romera** - [Website](http://www.josemarialuna.com)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/josemarialuna/RandomClustersGenerator.svg?style=for-the-badge
[contributors-url]: https://github.com/josemarialuna/RandomClustersGenerator/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/josemarialuna/RandomClustersGenerator.svg?style=for-the-badge
[forks-url]: https://github.com/josemarialuna/RandomClustersGenerator/network/members
[stars-shield]: https://img.shields.io/github/stars/josemarialuna/RandomClustersGenerator.svg?style=for-the-badge
[stars-url]: https://github.com/josemarialuna/RandomClustersGenerator/stargazers
[issues-shield]: https://img.shields.io/github/issues/josemarialuna/RandomClustersGenerator.svg?style=for-the-badge
[issues-url]: https://github.com/josemarialuna/RandomClustersGenerator/issues
[license-shield]: https://img.shields.io/github/license/josemarialuna/RandomClustersGenerator.svg?style=for-the-badge
[license-url]: https://github.com/josemarialuna/RandomClustersGenerator/blob/master/LICENSE.txt
