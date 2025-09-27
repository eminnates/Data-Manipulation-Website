import pandas as pd
import numpy as np
from flask_socketio import emit

def analyze_large_file_main(filepath, project_name, file_name, file_size_mb, app_instance):
    try:
        emit('data_analysis_status', {
            'status': 'progress',
            'message': f'Büyük dosya ({file_size_mb:.1f}MB) tespit edildi. Optimize analiz başlatılıyor...',
            'step': 1,
            'total_steps': 4
        })
        sample_size = 10000
        df_sample = pd.read_csv(filepath, nrows=sample_size)
        emit('data_analysis_status', {
            'status': 'progress',
            'message': f'Örnek veri ({sample_size} satır) yüklendi...',
            'step': 2,
            'total_steps': 4
        })
        total_columns = len(df_sample.columns)
        numeric_columns = df_sample.select_dtypes(include=['number']).columns.tolist()
        categorical_columns = df_sample.select_dtypes(include=['object']).columns.tolist()
        emit('data_analysis_status', {
            'status': 'progress',
            'message': 'Hızlı istatistik hesaplaması...',
            'step': 3,
            'total_steps': 4
        })
        column_statistics = []
        if numeric_columns:
            for col in numeric_columns[:2]:
                col_data = df_sample[col].dropna()
                if len(col_data) > 10:
                    Q1 = col_data.quantile(0.25)
                    Q3 = col_data.quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    clean_data = col_data[(col_data >= lower_bound) & (col_data <= upper_bound)]
                    if len(clean_data) > 0:
                        stats = clean_data.describe()
                        col_stats = {
                            'column_name': str(col),
                            'mean': float(stats['mean']) if np.isfinite(stats['mean']) else 0.0,
                            'std': min(float(stats['std']), 1_000_000) if np.isfinite(stats['std']) else 0.0,
                            'min': float(stats['min']) if np.isfinite(stats['min']) else 0.0,
                            'max': float(stats['max']) if np.isfinite(stats['max']) else 0.0,
                            'median': float(stats['50%']) if np.isfinite(stats['50%']) else 0.0,
                            'note': 'Büyük dosya sample + outlier temizleme'
                        }
                        column_statistics.append(col_stats)
        preview_df = df_sample.head(3).iloc[:, :5]
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
                    record[str(col)] = str(value)[:50]
            preview_records.append(record)
        emit('data_analysis_status', {
            'status': 'progress',
            'message': 'Büyük dosya analizi tamamlanıyor...',
            'step': 4,
            'total_steps': 4
        })
        analysis_results = {
            'basic_info': {
                'total_rows': 'Tahmini',
                'total_columns': int(total_columns),
                'file_size': round(float(file_size_mb), 2),
                'missing_values': 'Hesaplanmadı (büyük dosya)',
                'numeric_columns_count': int(len(numeric_columns)),
                'categorical_columns_count': int(len(categorical_columns)),
                'note': f'Büyük dosya - {sample_size} satırdan tahmin edildi'
            },
            'statistical_features': {
                'avg_skewness': 0.0,
                'avg_std': 0.0,
                'avg_variance': 0.0,
                'correlation_status': 'Büyük dosya - hesaplanmadı',
                'note': 'Performans için sınırlı analiz'
            },
            'column_statistics': column_statistics,
            'data_preview': {
                'columns': [str(col) for col in preview_df.columns],
                'data': preview_records,
                'total_rows': 'Tahmini',
                'note': 'Büyük dosya - ilk 3 satır ve 5 sütun'
            },
            'project_name': str(project_name),
            'file_name': str(file_name)
        }
        emit('data_analysis_complete', {
            'status': 'completed',
            'message': f'Büyük dosya analizi tamamlandı! ({file_size_mb:.1f}MB)',
            'results': analysis_results
        })
    except Exception as e:
        app_instance.logger.error(f'Large file analysis error: {str(e)}')
        emit('data_analysis_error', {
            'status': 'error',
            'message': f'Büyük dosya analiz hatası: {str(e)}',
            'error_type': 'large_file_error',
            'project_name': project_name,
            'file_name': file_name
        })