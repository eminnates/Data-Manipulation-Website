import os
import pandas as pd
import numpy as np
from flask_socketio import emit
from app.features.analysis.large_file_helpers import analyze_large_file_main

def analyze_data_background_main(filepath, project_name, file_name, app_instance):
    with app_instance.app_context():
        try:
            emit_analysis_status('started', 'Veri analizi başlatıldı...', project_name, file_name)
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Dosya bulunamadı: {filepath}")

            file_size_bytes = os.path.getsize(filepath)
            file_size_mb = file_size_bytes / (1024 * 1024)
            if file_size_mb > 100:
                app_instance.logger.info(f'Büyük dosya tespit edildi: {file_size_mb:.2f}MB')
                return analyze_large_file_main(filepath, project_name, file_name, file_size_mb, app_instance)

            df = load_csv(filepath)
            check_valid_df(df)

            emit_analysis_status('progress', 'Dosya başarıyla yüklendi...', project_name, file_name, 1, 6)
            emit_analysis_status('progress', 'Temel bilgiler hesaplanıyor...', project_name, file_name, 2, 6)
            basic_info = get_basic_info(df, file_size_mb)

            emit_analysis_status('progress', 'Sütun tipleri analiz ediliyor...', project_name, file_name, 3, 6)
            numeric_columns, categorical_columns = get_column_types(df)

            emit_analysis_status('progress', 'İstatistiksel özellikler hesaplanıyor...', project_name, file_name, 4, 6)
            stat_features, correlation_matrix = get_statistical_features(df, numeric_columns)

            emit_analysis_status('progress', 'Detaylı sütun istatistikleri hesaplanıyor...', project_name, file_name, 5, 6)
            column_statistics = get_column_statistics(df, numeric_columns)

            emit_analysis_status('progress', 'Veri önizlemesi hazırlanıyor...', project_name, file_name, 6, 6)
            data_preview = get_data_preview(df, basic_info['total_rows'], basic_info['total_columns'])

            analysis_results = {
                'basic_info': basic_info,
                'statistical_features': stat_features,
                'column_statistics': column_statistics,
                'data_preview': data_preview,
                'project_name': str(project_name),
                'file_name': str(file_name)
            }
            emit('data_analysis_complete', {
                'status': 'completed',
                'message': 'Veri analizi tamamlandı!',
                'results': analysis_results
            })

        except FileNotFoundError as e:
            emit_analysis_error('Dosya bulunamadı: ' + str(e), 'file_not_found', project_name, file_name)
        except ValueError as e:
            emit_analysis_error('Veri formatı hatası: ' + str(e), 'data_format', project_name, file_name)
        except MemoryError as e:
            emit_analysis_error('Dosya çok büyük. Lütfen daha küçük bir dosya yükleyin.', 'memory_error', project_name, file_name)
        except Exception as e:
            emit_analysis_error('Beklenmeyen hata: ' + str(e), 'general', project_name, file_name)

def emit_analysis_status(status, message, project_name, file_name, step=None, total_steps=None):
    data = {
        'status': status,
        'message': message,
        'project_name': project_name,
        'file_name': file_name
    }
    if step is not None and total_steps is not None:
        data['step'] = step
        data['total_steps'] = total_steps
    emit('data_analysis_status', data)

def emit_analysis_error(message, error_type, project_name, file_name):
    emit('data_analysis_error', {
        'status': 'error',
        'message': message,
        'error_type': error_type,
        'project_name': project_name,
        'file_name': file_name
    })

def load_csv(filepath):
    try:
        sample_df = pd.read_csv(filepath, nrows=100)
        if sample_df.empty:
            raise ValueError("Dosya boş veya geçersiz")
        return pd.read_csv(filepath)
    except pd.errors.EmptyDataError:
        raise ValueError("CSV dosyası boş")
    except pd.errors.ParserError as e:
        raise ValueError(f"CSV formatı hatalı: {str(e)}")
    except Exception as e:
        raise ValueError(f"Dosya okuma hatası: {str(e)}")

def check_valid_df(df):
    if len(df.columns) == 0:
        raise ValueError("Dosyada sütun bulunamadı")
    if len(df) == 0:
        raise ValueError("Dosyada veri bulunamadı")

def get_basic_info(df, file_size_mb):
    return {
        'total_rows': int(len(df)),
        'total_columns': int(len(df.columns)),
        'file_size': round(float(file_size_mb), 2),
        'missing_values': int(df.isnull().sum().sum()),
        'numeric_columns_count': int(len(df.select_dtypes(include=['number']).columns)),
        'categorical_columns_count': int(len(df.select_dtypes(include=['object']).columns))
    }

def get_column_types(df):
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
    categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
    return numeric_columns, categorical_columns

def get_statistical_features(df, numeric_columns):
    stat_features = {
        'avg_skewness': 0.0,
        'avg_std': 0.0,
        'avg_variance': 0.0,
        'correlation_status': 'Atlandı',
        'note': ''
    }
    correlation_matrix = None
    if numeric_columns:
        numeric_subset = numeric_columns[:5]
        numeric_df = df[numeric_subset]
        filtered_df = numeric_df.copy()
        for col in numeric_subset:
            Q1 = filtered_df[col].quantile(0.25)
            Q3 = filtered_df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            filtered_df[col] = filtered_df[col].where(
                (filtered_df[col] >= lower_bound) & (filtered_df[col] <= upper_bound)
            )
        skewness_values = filtered_df.skew().replace([np.inf, -np.inf], np.nan).fillna(0)
        stat_features['avg_skewness'] = float(skewness_values.mean()) if not skewness_values.empty else 0.0
        std_values = filtered_df.std().replace([np.inf, -np.inf], np.nan).fillna(0)
        stat_features['avg_std'] = float(std_values.where(std_values < 1_000_000, 0).mean()) if not std_values.empty else 0.0
        var_values = filtered_df.var().replace([np.inf, -np.inf], np.nan).fillna(0)
        stat_features['avg_variance'] = float(var_values.where(var_values < 1_000_000_000, 0).mean()) if not var_values.empty else 0.0
        if len(df) < 10000 and len(numeric_subset) <= 3:
            correlation_matrix = numeric_df.corr().fillna(0)
            stat_features['correlation_status'] = 'Hesaplanmış'
        else:
            stat_features['correlation_status'] = 'Performans için atlandı'
        stat_features['note'] = 'Büyük dosyalarda ilk 5 sütun analiz edilir'
    return stat_features, correlation_matrix

def get_column_statistics(df, numeric_columns):
    column_statistics = []
    for col in numeric_columns[:3]:
        col_data = df[col].dropna()
        if len(col_data) == 0:
            continue
        Q1 = col_data.quantile(0.25)
        Q3 = col_data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        clean_data = col_data[(col_data >= lower_bound) & (col_data <= upper_bound)]
        stats = clean_data.describe() if len(clean_data) > 0 else col_data.describe()
        col_stats = {
            'column_name': str(col),
            'mean': float(stats['mean']) if np.isfinite(stats['mean']) else 0.0,
            'std': float(stats['std']) if np.isfinite(stats['std']) and stats['std'] < 1_000_000 else 0.0,
            'min': float(stats['min']) if np.isfinite(stats['min']) else 0.0,
            'max': float(stats['max']) if np.isfinite(stats['max']) else 0.0,
            'median': float(stats['50%']) if np.isfinite(stats['50%']) else 0.0,
            'outliers_removed': int(len(col_data) - len(clean_data))
        }
        column_statistics.append(col_stats)
    return column_statistics

def get_data_preview(df, total_rows, total_columns):
    preview_df = df.head(5).iloc[:, :10]
    preview_records = []
    for _, row in preview_df.iterrows():
        record = {}
        for col in preview_df.columns:
            value = row[col]
            if pd.isna(value):
                record[str(col)] = None
            elif isinstance(value, (int, float)):
                if np.isfinite(value):
                    record[str(col)] = float(value) if isinstance(value, np.floating) else int(value)
                else:
                    record[str(col)] = None
            else:
                record[str(col)] = str(value)[:100]
        preview_records.append(record)
    return {
        'columns': [str(col) for col in preview_df.columns],
        'data': preview_records,
        'total_rows': int(total_rows),
        'note': 'İlk 5 satır ve 10 sütun gösteriliyor' if total_columns > 10 else None
    }