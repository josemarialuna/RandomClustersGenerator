import numpy as np 
import pandas as pd
import os
import warnings

warnings.filterwarnings('ignore')


numbers_of_dummies = [2, 8, 20]
MEAN = 1
STD_DEV = 0.05

files = os.listdir("data")

for filename in files:
    df = pd.read_csv(f'data/{filename}')
    for dummie in numbers_of_dummies:  
        for c in range(dummie):        
            df[f'd{c}'] = np.random.normal(loc=MEAN, scale=STD_DEV, size=len(df))
    
        df.to_csv(f'data/{filename[:-4]}_{dummie}d.csv',index=False)

print(df.head(100))
