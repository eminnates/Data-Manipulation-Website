import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os
import jinja2

# Ensure output directory exists
os.makedirs("outputs", exist_ok=True)

# Read the file
data = pd.read_csv(os.path.join("uploads", "read.csv"))

# Select the second column
column_name = data.columns[2]

# Plot with adjusted binwidth
plt.figure(figsize=(12, 6))
sns.histplot(data[column_name], binwidth=0.5, kde=True)  # Adjusted binwidth and added KDE
plt.title(f"Histogram of {column_name}")

# Save the plot
output_path = os.path.join("outputs", "output.png")
plt.savefig(output_path)
plt.close()
