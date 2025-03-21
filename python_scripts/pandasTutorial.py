import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
data= pd.read_csv(r"uploads\customers-1000.csv")
filter = (data['First Name'] == "Andrew") & (data['Index'] > 100) 
print(data[filter])
sns.barplot(data['First Name'])
plt.title('Overall vs. Wage')

plt.ylabel('Wage')

plt.xlabel('Overall')

plt.show()