from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import re

class Cleanse:
    def __init__(self, data):
        self.data = data

    def DeleteDupValues(self):
        """Remove duplicate rows."""
        self.data = self.data.drop_duplicates()

    def DropColumn(self, column_name):
        """Drop a specific column by name."""
        if column_name in self.data.columns:
            self.data = self.data.drop(columns=column_name)

    def StripSpecialChars(self):
        """Remove special characters from all string columns."""
        for col in self.data.select_dtypes(include=['object']).columns:
            self.data[col] = self.data[col].apply(lambda x: re.sub(r'[^\w\s]', '', x) if isinstance(x, str) else x)

    def NormalizeColumnValues(self):
        """Normalize specific column values (e.g., phone numbers, addresses)."""
        if 'phone' in self.data.columns:
            self.data['phone'] = self.data['phone'].apply(
                lambda x: re.sub(r'\D', '', x) if isinstance(x, str) else x
            )
            self.data['phone'] = self.data['phone'].apply(
                lambda x: f"{x[:3]}-{x[3:6]}-{x[6:]}" if isinstance(x, str) and len(x) == 10 else x
            )

    def FilterRows(self, condition):
        """Filter rows based on a condition."""
        # Extract column names from the condition
        condition_columns = [col.strip() for col in re.findall(r'\b\w+\b', condition) if col in self.data.columns]
        
        # Check if all columns in the condition exist in the DataFrame
        if all(col in self.data.columns for col in condition_columns):
            try:
                self.data = self.data.query(condition)
            except Exception as e:
                print(f"Error while applying the condition: {e}")
        else:
            missing_columns = [col for col in condition_columns if col not in self.data.columns]
            print(f"Error: The following columns are not found in the DataFrame: {missing_columns}")

    def DynamicFilter(self, filters):
        """
        Dynamically filter rows based on a dictionary of conditions.
        Example: filters = {'price': '> 100', 'quantity': '<= 50'}
        """
        for column, condition in filters.items():
            if column in self.data.columns:
                try:
                    self.data = self.data.query(f"{column} {condition}")
                except Exception as e:
                    print(f"Error while applying the condition on column '{column}': {e}")
            else:
                print(f"Error: Column '{column}' not found in the DataFrame.")
class Manipulation:
    def __init__(self, data):
        self.data = data

    def detectAndDeleteOutliers(self):
        """Detect outliers in all numeric columns using IQR method."""
        for column_name in self.data.select_dtypes(include=[np.number]).columns:
            Q1 = self.data[column_name].quantile(0.25)
            Q3 = self.data[column_name].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = self.data[(self.data[column_name] < lower_bound) | (self.data[column_name] > upper_bound)]
            
            if not outliers.empty:
                self.data = self.data[(self.data[column_name] >= lower_bound) & (self.data[column_name] <= upper_bound)]
            else:
                print(f"Column '{column_name}' has no outliers.")

        def scaleValues(self, column_name, min_val=0, max_val=1):
            """Scale numeric column values to a specific range."""
            if column_name in self.data.columns and pd.api.types.is_numeric_dtype(self.data[column_name]):
                col_min = self.data[column_name].min()
                col_max = self.data[column_name].max()
                self.data[column_name] = (self.data[column_name] - col_min) / (col_max - col_min) * (max_val - min_val) + min_val
            else:
                print(f"Error: Column '{column_name}' is not numeric or not found in the DataFrame.")


    def logTransform(self, column_name):
        """Apply log transformation to a numeric column."""
        sorted_column = self.data.sort_values(by=column_name, ascending=True)
        if column_name in self.data.columns and pd.api.types.is_numeric_dtype(self.data[column_name]):
            self.data[column_name] = np.log1p(self.data[column_name])
        else:
            print(f"Error: Column '{column_name}' is not numeric or not found in the DataFrame.")
class Augmentation:
    def __init__(self, data):
        self.data = data
        self.columns = list(data.columns) 

    def sortValues(self, column_name, ascending=True):
        """Sort the DataFrame by a specific column."""
        if column_name in self.data.columns:
            self.data = self.data.sort_values(by=column_name, ascending=ascending)
        else:
            print(f"Error: Column '{column_name}' not found in the DataFrame.")

    def addNoise(self, column_name, noise_level=0.01):
        """Add random noise to a numeric column."""
        if column_name in self.data.columns and pd.api.types.is_numeric_dtype(self.data[column_name]):
            noise = np.random.normal(0, noise_level, self.data[column_name].shape)
            self.data[column_name] += noise
        else:
            print(f"Error: Column '{column_name}' is not numeric or not found in the DataFrame.")

    def generateSyntheticData(self, num_samples=10):
        """Generate synthetic rows by sampling existing data."""
        synthetic_data = self.data.sample(n=num_samples, replace=True).reset_index(drop=True)
        self.data = pd.concat([self.data, synthetic_data], ignore_index=True)

    def categoricalToNumeric(self, column_name):
        """Convert a categorical column to numeric using label encoding."""
        if column_name in self.data.columns and pd.api.types.is_string_dtype(self.data[column_name]):
            self.data[column_name] = self.data[column_name].astype('category').cat.codes
        else:
            print(f"Error: Column '{column_name}' is not categorical or not found in the DataFrame.")


    def combineColumns(self, columns, new_column_name, separator=' '):
        """Combine multiple columns into a single column."""
        if all(col in self.data.columns for col in columns):
            self.data[new_column_name] = self.data[columns].astype(str).apply(separator.join, axis=1)
        else:
            missing_columns = [col for col in columns if col not in self.data.columns]
            print(f"Error: The following columns are not found in the DataFrame: {missing_columns}")

    def timeSeriesShift(self, column_name, periods=1):
        """Shift a column in a time series by a specified number of periods."""
        if column_name in self.data.columns:
            self.data[f"{column_name}_shifted"] = self.data[column_name].shift(periods)
        else:
            print(f"Error: Column '{column_name}' not found in the DataFrame.")

    def augmentWithExternalData(self, external_data, on_column):
        """Augment the DataFrame with external data based on a common column."""
        if on_column in self.data.columns and on_column in external_data.columns:
            self.data = self.data.merge(external_data, on=on_column, how='left')
        else:
            print(f"Error: Column '{on_column}' not found in one of the DataFrames.")

    def autoAugment(self):
        """Automatically apply a series of augmentation techniques."""
        # Example augmentations
        if(len(self.data) < 200):
            self.generateSyntheticData(num_samples=10)
        
        '''self.sortValues('date', ascending=True)
        self.addNoise('price', noise_level=0.05)
        self.generateSyntheticData(num_samples=5)
        self.categoricalToNumeric('category')
        self.scaleValues('price', min_val=0, max_val=1)
        self.combineColumns(['date', 'category'], 'combined_info', separator='_')
        self.timeSeriesShift('price', periods=1)'''


