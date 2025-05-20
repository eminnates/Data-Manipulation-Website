from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import re
from pandas.api.types import is_numeric_dtype, is_string_dtype

class Cleanse:
    def __init__(self, data):
        self.data = data

    # 1. Boşluk ve özel karakter temizliği
    def RemoveWhitespace(self):
        """Tüm string sütunlardaki baştaki ve sondaki boşlukları temizler."""
        for col in self.data.select_dtypes(include=['object']).columns:
            self.data[col] = self.data[col].str.strip()

    def StripSpecialChars(self):
        """Remove special characters from all string columns."""
        for col in self.data.select_dtypes(include=['object']).columns:
            self.data[col] = self.data[col].apply(lambda x: re.sub(r'[^\w\s]', '', x) if isinstance(x, str) else x)

    # 2. Küçük harfe çevirme
    def LowercaseColumns(self):
        """Tüm string sütunlardaki değerleri küçük harfe çevirir."""
        for col in self.data.select_dtypes(include=['object']).columns:
            self.data[col] = self.data[col].str.lower()

    # 3. Hatalı tip düzeltme
    def FixNumericColumn(self, column_name, fillna_method=None):
        """
        Bir sütunda sayısal olmayan değerleri tespit eder ve düzeltir.
        fillna_method: None, 'mean', 'median', 'mode', 'zero' (None ise sadece NaN bırakır)
        """
        if column_name in self.data.columns:
            before = self.data[column_name].copy()
            self.data[column_name] = pd.to_numeric(self.data[column_name], errors='coerce')
            n_fixed = (before != self.data[column_name]).sum()
            if n_fixed > 0:
                print(f"{column_name} sütununda {n_fixed} adet sayısal olmayan değer düzeltildi (NaN yapıldı).")
            if fillna_method:
                if fillna_method == 'mean':
                    self.data[column_name] = self.data[column_name].fillna(self.data[column_name].mean())
                elif fillna_method == 'median':
                    self.data[column_name] = self.data[column_name].fillna(self.data[column_name].median())
                elif fillna_method == 'mode':
                    self.data[column_name] = self.data[column_name].fillna(self.data[column_name].mode()[0])
                elif fillna_method == 'zero':
                    self.data[column_name] = self.data[column_name].fillna(0)
        else:
            print(f"Column '{column_name}' not found.")

    def AutoFixNumericColumns(self, fillna_method=None):
        """
        Tüm sayısal olması beklenen sütunlarda otomatik olarak sayısal olmayan değerleri NaN yapar ve istenirse doldurur.
        """
        keywords = ['age', 'yas', 'price', 'fiyat', 'score', 'puan', 'adet', 'count', 'total', 'sum', 'number', 'num', 'quantity', 'amount']
        for col in self.data.columns:
            if any(key in col.lower() for key in keywords):
                before = self.data[col].copy()
                self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
                n_fixed = (before != self.data[col]).sum()
                if n_fixed > 0:
                    print(f"{col} sütununda {n_fixed} adet sayısal olmayan değer düzeltildi (NaN yapıldı).")
                if fillna_method:
                    if fillna_method == 'mean':
                        self.data[col] = self.data[col].fillna(self.data[col].mean())
                    elif fillna_method == 'median':
                        self.data[col] = self.data[col].fillna(self.data[col].median())
                    elif fillna_method == 'mode':
                        self.data[col] = self.data[col].fillna(self.data[col].mode()[0])
                    elif fillna_method == 'zero':
                        self.data[col] = self.data[col].fillna(0)

    # 4. Eksik değer doldurma veya sütun silme
    def FillMissing(self, column_name, method='mean', value=None):
        """
        Eksik değerleri doldurur.
        method: 'mean', 'median', 'mode', 'value'
        value: method 'value' ise kullanılacak değer
        """
        if column_name in self.data.columns:
            if method == 'mean':
                self.data[column_name] = self.data[column_name].fillna(self.data[column_name].mean())
            elif method == 'median':
                self.data[column_name] = self.data[column_name].fillna(self.data[column_name].median())
            elif method == 'mode':
                self.data[column_name] = self.data[column_name].fillna(self.data[column_name].mode()[0])
            elif method == 'value' and value is not None:
                self.data[column_name] = self.data[column_name].fillna(value)
            else:
                print(f"Unknown method: {method}")
        else:
            print(f"Column '{column_name}' not found.")

    def RemoveHighNullColumns(self, threshold=0.5):
        """
        Belirli orandan fazla eksik değeri olan sütunları kaldırır.
        threshold: 0.5 -> %50'den fazla eksik varsa sil
        """
        null_ratio = self.data.isnull().mean()
        to_drop = null_ratio[null_ratio > threshold].index.tolist()
        self.data = self.data.drop(columns=to_drop)
        if to_drop:
            print(f"Removed columns with high null ratio: {to_drop}")

    # 5. Tekrarlı satır/sütun temizliği
    def DeleteDupValues(self):
        """Remove duplicate rows."""
        self.data = self.data.drop_duplicates()

    def RemoveConstantColumns(self):
        """Tüm değerleri aynı olan sütunları kaldırır."""
        nunique = self.data.nunique()
        constant_cols = nunique[nunique == 1].index.tolist()
        self.data = self.data.drop(columns=constant_cols)
        if constant_cols:
            print(f"Removed constant columns: {constant_cols}")

    # 6. Aykırı değer işlemleri
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

    # 7. Alan bazlı özel temizlik
    def CleanEmails(self, column_name='email'):
        """
        Email sütunundaki hatalı değerleri düzeltir:
        - 'none' içerenleri siler (NaN yapar)
        - '[at]' ifadesini '@' ile değiştirir
        - E-posta formatına uymayanları siler (NaN yapar)
        """
        if column_name in self.data.columns:
            def fix_email(val):
                if not isinstance(val, str):
                    return np.nan
                v = val.strip().lower()
                if 'none' in v:
                    return np.nan
                v = v.replace('[at]', '@')
                if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", v):
                    return np.nan
                return v
            self.data[column_name] = self.data[column_name].apply(fix_email)
        else:
            print(f"Column '{column_name}' not found.")

    def NormalizeColumnValues(self):
        """Normalize specific column values (e.g., phone numbers, addresses)."""
        if 'phone' in self.data.columns:
            self.data['phone'] = self.data['phone'].apply(
                lambda x: re.sub(r'\D', '', x) if isinstance(x, str) else x
            )
            self.data['phone'] = self.data['phone'].apply(
                lambda x: f"{x[:3]}-{x[3:6]}-{x[6:]}" if isinstance(x, str) and len(x) == 10 else x
            )

    def AutoRemoveDigitsFromStringColumns(self):
        """
        İsim, soyisim, şehir, ülke, adres gibi sütunlarda rakamları otomatik olarak siler.
        """
        string_columns = [col for col in self.data.select_dtypes(include=['object']).columns]
        keywords = ['name', 'isim', 'surname', 'soyisim', 'city', 'şehir', 'country', 'ülke', 'address', 'adres']
        for col in string_columns:
            if any(key in col.lower() for key in keywords):
                self.data[col] = self.data[col].apply(lambda x: re.sub(r'\d+', '', x) if isinstance(x, str) else x)

    # 8. Filtreleme ve son kontroller
    def FilterRows(self, condition):
        """Filter rows based on a condition."""
        condition_columns = [col.strip() for col in re.findall(r'\b\w+\b', condition) if col in self.data.columns]
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

    # Diğer yardımcı fonksiyonlar (gerekirse ekleyebilirsin)
    def DropColumn(self, column_name):
        """Drop a specific column by name."""
        if column_name in self.data.columns:
            self.data = self.data.drop(columns=column_name)

    def RemoveDuplicatesByColumns(self, columns):
        """Belirli sütunlara göre tekrar eden satırları siler."""
        self.data = self.data.drop_duplicates(subset=columns)

    def ReplaceValues(self, column_name, to_replace, value):
        """Bir sütunda belirli değerleri başka bir değerle değiştirir."""
        if column_name in self.data.columns:
            self.data[column_name] = self.data[column_name].replace(to_replace, value)
        else:
            print(f"Column '{column_name}' not found.")

class Manipulation:
    def __init__(self, data):
        self.data = data

    @staticmethod
    def choose_column_operations(df, skew_threshold=1, outlier_ratio_threshold=0.05):
        """
        Scans all numeric columns and suggests 'log', 'outlier', or 'none' for each.
        Returns a dict: {column_name: ['log', 'outlier', ...]}
        """
        operations = {}
        for col in df.select_dtypes(include=[np.number]).columns:
            ops = []
            # Calculate skewness
            skew = df[col].skew()
            # Detect outliers using IQR
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            outlier_count = ((df[col] < lower) | (df[col] > upper)).sum()
            outlier_ratio = outlier_count / len(df)
            # Decide
            if skew > skew_threshold:
                ops.append('log')
            if outlier_ratio > outlier_ratio_threshold:
                ops.append('outlier')
            if not ops:
                ops.append('none')
            operations[col] = ops
        return operations

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
            if column_name in self.data.columns and is_numeric_dtype(self.data[column_name]):
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
        if column_name in self.data.columns and is_string_dtype(self.data[column_name]):
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

    def suggest_operations(self):
        '''
        Suggest augmentation operations for each column in the DataFrame.

        For numeric columns, it suggests adding noise.
        For string columns, it suggests converting to numeric.
        If the DataFrame has less than 200 rows, it suggests generating synthetic data.
        '''
        operations = {}
        for col in self.data.columns:
            ops = []
            if pd.api.types.is_numeric_dtype(self.data[col]):
                ops.append('add_noise')
            if pd.api.types.is_string_dtype(self.data[col]):
                ops.append('categorical_to_numeric')
            if not ops:
                ops.append('none')
            # Eğer veri küçükse, her kolona synthetic data önerisi ekle
            if len(self.data) < 200:
                ops.append('generate_synthetic_data')
            operations[col] = ops
        return operations



