from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import re
from pandas.api.types import is_numeric_dtype, is_string_dtype

class Cleanse:
    def __init__(self, data):
        self.data = data

    # 1. Boşluk ve özel karakter temizliği
    def RemoveWhitespace(self, type='all', columns=None):
        """
        String sütunlardaki boşlukları temizler.
        type: 'leading', 'trailing', 'multiple', 'all'
        columns: Temizlenecek sütun listesi, None ise tüm string sütunlar
        """
        if columns is None:
            target_columns = self.data.select_dtypes(include=['object']).columns
        elif isinstance(columns, str):
            target_columns = [columns] if columns in self.data.columns else []
        else:
            target_columns = [col for col in columns if col in self.data.columns]
        
        for col in target_columns:
            if type == 'leading':
                # Sadece baştaki boşlukları temizle
                self.data[col] = self.data[col].str.lstrip()
            elif type == 'trailing':
                # Sadece sondaki boşlukları temizle
                self.data[col] = self.data[col].str.rstrip()
            elif type == 'multiple':
                # Çoklu boşlukları tek boşluğa dönüştür
                self.data[col] = self.data[col].str.replace(r'\s+', ' ', regex=True)
            elif type == 'all':
                # Tüm boşlukları kaldır
                self.data[col] = self.data[col].str.replace(r'\s+', '', regex=True)
            else:
                # Varsayılan: baş ve sondaki boşlukları temizle
                self.data[col] = self.data[col].str.strip()

    def StripSpecialChars(self, type='all', columns=None, custom_chars=None):
        """
        String sütunlardaki özel karakterleri temizler.
        type: 'punctuation', 'numbers', 'symbols', 'all', 'custom'
        columns: Temizlenecek sütun listesi, None ise tüm string sütunlar
        custom_chars: type='custom' ise kaldırılacak karakter dizisi (örn: "@#$%")
        """
        if columns is None:
            target_columns = self.data.select_dtypes(include=['object']).columns
        elif isinstance(columns, str):
            target_columns = [columns] if columns in self.data.columns else []
        else:
            target_columns = [col for col in columns if col in self.data.columns]
        
        for col in target_columns:
            if type == 'punctuation':
                # Sadece noktalama işaretlerini kaldır
                self.data[col] = self.data[col].apply(lambda x: re.sub(r'[^\w\s]', '', x) if isinstance(x, str) else x)
            elif type == 'numbers':
                # Sadece rakamları kaldır
                self.data[col] = self.data[col].apply(lambda x: re.sub(r'\d', '', x) if isinstance(x, str) else x)
            elif type == 'symbols':
                # Sadece sembol karakterleri kaldır
                self.data[col] = self.data[col].apply(lambda x: re.sub(r'[^\w\s.,!?;:]', '', x) if isinstance(x, str) else x)
            elif type == 'custom' and custom_chars:
                # Belirtilen karakterleri kaldır
                escaped_chars = re.escape(custom_chars)
                pattern = f'[{escaped_chars}]'
                self.data[col] = self.data[col].apply(lambda x: re.sub(pattern, '', x) if isinstance(x, str) else x)
            elif type == 'all':
                # Tüm özel karakterleri kaldır (sadece harf ve boşluk bırak)
                self.data[col] = self.data[col].apply(lambda x: re.sub(r'[^\w\s]', '', x) if isinstance(x, str) else x)
            else:
                # Varsayılan: tüm özel karakterleri kaldır
                self.data[col] = self.data[col].apply(lambda x: re.sub(r'[^\w\s]', '', x) if isinstance(x, str) else x)

    # 2. Küçük harfe çevirme
    def LowercaseColumns(self, type='lower', columns=None):
        """
        String sütunlardaki değerleri büyük/küçük harfe çevirir.
        type: 'lower', 'upper', 'title', 'capitalize'
        columns: Dönüştürülecek sütun listesi, None ise tüm string sütunlar
        """
        if columns is None:
            target_columns = self.data.select_dtypes(include=['object']).columns
        elif isinstance(columns, str):
            target_columns = [columns] if columns in self.data.columns else []
        else:
            target_columns = [col for col in columns if col in self.data.columns]
        
        for col in target_columns:
            if type == 'lower':
                self.data[col] = self.data[col].str.lower()
            elif type == 'upper':
                self.data[col] = self.data[col].str.upper()
            elif type == 'title':
                self.data[col] = self.data[col].str.title()
            elif type == 'capitalize':
                self.data[col] = self.data[col].str.capitalize()
            else:
                # Varsayılan: küçük harfe çevir
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

    # Diğer yardımcı fonksiyonlar (gerekirse ekleyebilirsin)
    def DropColumn(self, column_name):
        """Drop a specific column by name."""
        if column_name in self.data.columns:
            self.data = self.data.drop(columns=column_name)


    def ReplaceValues(self, column_name, to_replace, value):
        """Bir sütunda belirli değerleri başka bir değerle değiştirir."""
        if column_name in self.data.columns:
            self.data[column_name] = self.data[column_name].replace(to_replace, value)
        else:
            print(f"Column '{column_name}' not found.")

    def DetectChanges(self, operation_type, parameters=None):
        if parameters is None:
            parameters = {}

        current_rows = len(self.data)
        # DÜZELTME: İşlemden önce verinin bir kopyasını alarak içerik karşılaştırması yapmaya hazırlan.
        before_data = self.data.copy()
        
        # Spesifik işlem türleri için özel hesaplamalar
        if operation_type == 'RemoveWhitespace':
            return self._calculate_whitespace_effects(parameters)
        elif operation_type == 'StripSpecialChars':
            return self._calculate_special_chars_effects(parameters)
        elif operation_type == 'LowercaseColumns':
            return self._calculate_case_effects(parameters)
        elif operation_type == 'DeleteDupValues':
            return self._calculate_duplicate_effects(parameters)
        elif operation_type == 'DropColumn':
            return self._calculate_drop_column_effects(parameters)
        elif operation_type == 'AutoFixNumericColumns':
            return self._calculate_numeric_fix_effects(parameters)
        
        # Diğer işlemler için genel handler
        operation_handlers = {
            'FixNumericColumn': self.FixNumericColumn,
            'FillMissing': self.FillMissing,
            'RemoveHighNullColumns': self.RemoveHighNullColumns,
            'RemoveConstantColumns': self.RemoveConstantColumns,
            'CleanEmails': self.CleanEmails,
            'NormalizeColumnValues': self.NormalizeColumnValues,
            'AutoRemoveDigitsFromStringColumns': self.AutoRemoveDigitsFromStringColumns,
            'FilterRows': self.FilterRows,
            'DynamicFilter': self.DynamicFilter,
            'RemoveDuplicatesByColumns': self.RemoveDuplicatesByColumns,
            'ReplaceValues': self.ReplaceValues,
            'SampleData': self.SampleData,
        }

        if operation_type in operation_handlers:
            try:
                operation_handlers[operation_type](**parameters)
            except TypeError as e:
                print(f"Hata: '{operation_type}' operasyonu yanlış parametrelerle çağrıldı. Detay: {e}")
                return None
            except Exception as e:
                print(f"'{operation_type}' işlemi sırasında beklenmedik bir hata oluştu: {e}")
                return None
        else:
            print(f"Desteklenmeyen operasyon tipi: {operation_type}")
            return None

        # DÜZELTME: Etkilenen satır sayısını, hem satır silme hem de içerik değişikliğini dikkate alarak hesapla.
        if current_rows != len(self.data):
            # Eğer satır sayısı değiştiyse (örn: DeleteDupValues, FilterRows), etki satır farkıdır.
            affected_rows = current_rows - len(self.data)
        else:
            # Eğer satır sayısı aynıysa, içerik değişikliğini kontrol et.
            try:
                # Önce DataFrame'lerin aynı boyutta olduğunu kontrol et
                if before_data.shape == self.data.shape:
                    # İndeks ve sütunların aynı olduğunu kontrol et
                    if before_data.index.equals(self.data.index) and before_data.columns.equals(self.data.columns):
                        # NaN değerleri dikkate alarak karşılaştırma yap
                        comparison = before_data.compare(self.data, align_axis=1, keep_shape=True, keep_equal=False)
                        if not comparison.empty:
                            # Değişiklik olan satırları bul
                            affected_rows = len(comparison.index.unique())
                        else:
                            affected_rows = 0
                    else:
                        # İndeks veya sütunlar farklıysa, güvenli karşılaştırma yap
                        affected_rows = 0
                        try:
                            # Ortak sütunları bul
                            common_cols = before_data.columns.intersection(self.data.columns)
                            if len(common_cols) > 0:
                                # Ortak satırları bul
                                common_idx = before_data.index.intersection(self.data.index)
                                if len(common_idx) > 0:
                                    before_subset = before_data.loc[common_idx, common_cols]
                                    after_subset = self.data.loc[common_idx, common_cols]
                                    # Değişiklikleri kontrol et
                                    changes = (before_subset != after_subset).any(axis=1)
                                    affected_rows = changes.sum()
                        except Exception:
                            # Karşılaştırma başarısız olursa, tüm satırları etkilenmiş say
                            affected_rows = min(current_rows, len(self.data))
                else:
                    # Farklı boyuttaki DataFrame'ler için basit yaklaşım
                    affected_rows = abs(current_rows - len(self.data))
            except Exception:
                # Karşılaştırma başarısız olursa, değişiklik varsay
                affected_rows = max(current_rows, len(self.data))

        remaining_rows = len(self.data)
        affected_percentage = (affected_rows / current_rows * 100) if current_rows > 0 else 0
        
        return {
            'current_rows': current_rows,
            'affected_rows': int(affected_rows), # Sonucun integer olduğundan emin ol
            'remaining_rows': remaining_rows,
            'affected_percentage': round(affected_percentage, 2)
        }

    # DÜZELTME: Fonksiyonu doğru bir sınıf metodu olarak yeniden yaz
    def SampleData(self, sample_size=0.1, random_state=None, stratify_column=None):
        """
        Veri setinden bir örneklem alır. Metod imzası, DetectChanges ile uyumlu olacak şekilde güncellenmiştir.
        Bu metod, self.data'yı doğrudan günceller ve bir değer döndürmez.
        """
        # DÜZELTME: Parametre olarak gelen 'data' yerine sınıfın kendi 'self.data'sını kullan
        data_to_use = self.data.copy()
        total_rows = len(data_to_use)
        
        # Örneklem boyutunu belirle
        if isinstance(sample_size, float) and 0 < sample_size < 1:
            n_samples = int(total_rows * sample_size)
        elif isinstance(sample_size, int) and sample_size > 0:
            n_samples = min(sample_size, total_rows)
        else:
            n_samples = int(total_rows * 0.1)  # Geçersizse varsayılan olarak %10 al

        # Eğer stratify_column belirtilmişse ve geçerliyse katmanlı örnekleme yap
        if stratify_column and stratify_column in data_to_use.columns:
            try:
                # Her gruptan en az 1 örnek alınmasını sağla (eğer mümkünse)
                self.data = data_to_use.groupby(stratify_column, group_keys=False).apply(
                    lambda x: x.sample(n=min(len(x), max(1, int(n_samples * len(x) / total_rows))), 
                                       random_state=random_state)
                ).reset_index(drop=True)
            except Exception as e:
                print(f"Katmanlı örnekleme başarısız oldu: {e}. Normal rastgele örneklemeye geçiliyor.")
                self.data = data_to_use.sample(n=n_samples, random_state=random_state)
        else:
            # Normal rastgele örnekleme
            self.data = data_to_use.sample(n=n_samples, random_state=random_state)
        # Özel hesaplama metodları - DetectChanges için
    def _calculate_whitespace_effects(self, parameters):
        """RemoveWhitespace işlemi için etki hesaplama"""
        whitespace_type = parameters.get('type', 'all')
        columns = parameters.get('columns', [])
        
        if not columns:
            target_columns = self.data.select_dtypes(include=['object']).columns
        else:
            target_columns = [col for col in columns if col in self.data.columns]
        
        affected_rows = 0
        
        for col in target_columns:
            if col in self.data.columns:
                try:
                    # Boşluk içeren satırları say
                    if whitespace_type == 'leading':
                        # Baştaki boşluk
                        affected_rows += self.data[col].str.match(r'^\s+').fillna(False).sum()
                    elif whitespace_type == 'trailing':
                        # Sondaki boşluk
                        affected_rows += self.data[col].str.match(r'\s+$').fillna(False).sum()
                    elif whitespace_type == 'multiple':
                        # Çoklu boşluk
                        affected_rows += self.data[col].str.contains(r'\s{2,}').fillna(False).sum()
                    elif whitespace_type == 'all':
                        # Herhangi bir boşluk
                        affected_rows += self.data[col].str.contains(r'\s').fillna(False).sum()
                    else:
                        # Baş/son boşluk
                        affected_rows += (self.data[col].str.match(r'^\s+').fillna(False) | self.data[col].str.match(r'\s+$').fillna(False)).sum()
                except:
                    # Hata durumunda o sütunu atla
                    continue
        
        return {
            'current_rows': len(self.data),
            'affected_rows': int(affected_rows),
            'remaining_rows': len(self.data),
            'affected_percentage': round((affected_rows / len(self.data) * 100) if len(self.data) > 0 else 0, 2)
        }
    
    def _calculate_special_chars_effects(self, parameters):
        """StripSpecialChars işlemi için etki hesaplama"""
        special_type = parameters.get('type', 'all')
        columns = parameters.get('columns', [])
        custom_chars = parameters.get('custom_chars', None)
        
        if not columns:
            target_columns = self.data.select_dtypes(include=['object']).columns
        else:
            target_columns = [col for col in columns if col in self.data.columns]
        
        affected_rows = 0
        
        for col in target_columns:
            if col in self.data.columns:
                try:
                    if special_type == 'punctuation':
                        # Noktalama işaretleri
                        affected_rows += self.data[col].str.contains(r'[^\w\s]').fillna(False).sum()
                    elif special_type == 'numbers':
                        # Rakamlar
                        affected_rows += self.data[col].str.contains(r'\d').fillna(False).sum()
                    elif special_type == 'symbols':
                        # Semboller
                        affected_rows += self.data[col].str.contains(r'[^\w\s.,!?;:]').fillna(False).sum()
                    elif special_type == 'custom' and custom_chars:
                        # Özel karakterler
                        pattern = f'[{re.escape(custom_chars)}]'
                        affected_rows += self.data[col].str.contains(pattern).fillna(False).sum()
                    else:
                        # Tüm özel karakterler
                        affected_rows += self.data[col].str.contains(r'[^\w\s]').fillna(False).sum()
                except:
                    # Hata durumunda o sütunu atla
                    continue
        
        return {
            'current_rows': len(self.data),
            'affected_rows': int(affected_rows),
            'remaining_rows': len(self.data),
            'affected_percentage': round((affected_rows / len(self.data) * 100) if len(self.data) > 0 else 0, 2)
        }
    
    def _calculate_case_effects(self, parameters):
        """LowercaseColumns işlemi için etki hesaplama"""
        case_type = parameters.get('type', 'lower')
        columns = parameters.get('columns', [])
        
        if not columns:
            target_columns = self.data.select_dtypes(include=['object']).columns
        else:
            target_columns = [col for col in columns if col in self.data.columns]
        
        affected_rows = 0
        
        for col in target_columns:
            if col in self.data.columns:
                try:
                    if case_type == 'lower':
                        # Büyük harf içeren satırları say
                        affected_rows += self.data[col].str.contains(r'[A-Z]').fillna(False).sum()
                    elif case_type == 'upper':
                        # Küçük harf içeren satırları say
                        affected_rows += self.data[col].str.contains(r'[a-z]').fillna(False).sum()
                    elif case_type in ['title', 'capitalize']:
                        # Başlık formatında olmayan satırları say
                        affected_rows += (~self.data[col].str.match(r'^[A-Z][a-z]*')).fillna(True).sum()
                except:
                    # Hata durumunda o sütunu atla
                    continue
        
        return {
            'current_rows': len(self.data),
            'affected_rows': int(affected_rows),
            'remaining_rows': len(self.data),
            'affected_percentage': round((affected_rows / len(self.data) * 100) if len(self.data) > 0 else 0, 2)
        }
    
    def _calculate_duplicate_effects(self, parameters):
        """DeleteDupValues işlemi için etki hesaplama"""
        duplicate_type = parameters.get('type', 'all')
        columns = parameters.get('columns', [])
        
        if duplicate_type == 'all':
            # Tüm satırları kontrol et
            duplicate_count = self.data.duplicated().sum()
        else:
            # Belirli sütunları kontrol et
            if columns:
                duplicate_count = self.data.duplicated(subset=columns).sum()
            else:
                duplicate_count = self.data.duplicated().sum()
        
        return {
            'current_rows': len(self.data),
            'affected_rows': int(duplicate_count),
            'remaining_rows': len(self.data) - duplicate_count,
            'affected_percentage': round((duplicate_count / len(self.data) * 100) if len(self.data) > 0 else 0, 2)
        }
    
    def _calculate_drop_column_effects(self, parameters):
        """DropColumn işlemi için etki hesaplama"""
        columns = parameters.get('columns', [])
        
        if isinstance(columns, str):
            columns = [columns]
        
        # Var olan sütunları say
        existing_columns = [col for col in columns if col in self.data.columns]
        
        return {
            'current_rows': len(self.data),
            'affected_rows': len(existing_columns),  # Etkilenen sütun sayısı
            'remaining_rows': len(self.data),
            'affected_percentage': round((len(existing_columns) / len(self.data.columns) * 100) if len(self.data.columns) > 0 else 0, 2)
        }
    
    def _calculate_numeric_fix_effects(self, parameters):
        """AutoFixNumericColumns işlemi için etki hesaplama"""
        affected_rows = 0
        keywords = ['age', 'yas', 'price', 'fiyat', 'score', 'puan', 'adet', 'count', 'total', 'sum', 'number', 'num', 'quantity', 'amount']
        
        for col in self.data.columns:
            if any(key in col.lower() for key in keywords):
                # Sayısal olmayan değerleri say
                try:
                    numeric_conversion = pd.to_numeric(self.data[col], errors='coerce')
                    non_numeric_count = numeric_conversion.isna().sum() - self.data[col].isna().sum()
                    affected_rows += non_numeric_count
                except:
                    continue
        
        return {
            'current_rows': len(self.data),
            'affected_rows': int(affected_rows),
            'remaining_rows': len(self.data),
            'affected_percentage': round((affected_rows / len(self.data) * 100) if len(self.data) > 0 else 0, 2)
        }





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

