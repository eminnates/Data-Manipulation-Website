# importing libraries
import pandas as pd
import scipy
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import seaborn as sns
import matplotlib.pyplot as plt
df = pd.read_csv("uploads\\Amazon stock data 2000-2025.csv")
print(df.isnull().sum())
print(df.describe())
fig, axs = plt.subplots(6,2,dpi=95,figsize=(15,35))
axs = axs.flatten() #2d yi 1d yap
i=0
for col in df.columns[1:]:
    df[col] = np.log1p(df[col])
    axs[i*2].boxplot(df[col], vert=False)
    axs[i*2].set_ylabel(col)
    q1, q3 = np.percentile(df[col], [25, 75])
    iqr = q3 - q1
    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)
    clean_data = df[(df[col] >= lower_bound) 
                    & (df[col] <= upper_bound)]
    axs[i*2+1].boxplot(clean_data[col], vert=False)
    axs[i*2+1].set_ylabel('cleaned_' + col)
    i+=1
    
plt.show()