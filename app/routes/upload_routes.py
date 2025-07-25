from flask import Blueprint, request, jsonify, current_app
import os
import pandas as pd
import numpy as np
import threading
from app.utils.file_utils import allowed_file
from python_scripts.getHead import GetHead
from python_scripts.getColumns import GetColumns
from flask_cors import cross_origin
from app.features.websocket.extensions import socketio

upload_blueprint = Blueprint('upload', __name__)

@upload_blueprint.route('/<projectName>', methods=['POST'])
@cross_origin()
def upload_file(projectName):
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Filename is empty'}), 400
    
    if allowed_file(file.filename):
        project_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], projectName)
        os.makedirs(project_folder, exist_ok=True)

        filepath = os.path.join(project_folder, file.filename)
        file.save(filepath)

        # Eventlet Green Thread ile analiz başlat
        app_instance = current_app._get_current_object()
        import eventlet
        eventlet.spawn(analyze_data_background, filepath, projectName, file.filename, app_instance)

        return jsonify({
            'status': 'success', 
            'message': 'File uploaded successfully. Data analysis started in background.', 
            'file_name': file.filename,
            'project_name': projectName,
            'file_path': filepath,
            'analysis_started': True
        }), 200
    else:
        return jsonify({'status': 'error', 'message': 'File type not allowed'}), 400


@upload_blueprint.route('/get-head-api', methods=['POST'])
def get_head_api():
    try:
        # JSON içindeki sample alanını al
        data = request.get_json()
        if not data or 'sample' not in data:
            return jsonify({'status': 'error', 'message': 'sample verisi eksik'}), 400
        
        sample_text = data['sample']
        
        # Pandas ile sample CSV'yi oku
        from io import StringIO
        sample_io = StringIO(sample_text)
        df = pd.read_csv(sample_io)

        # İlk 10 satır (zaten öyle geliyor ama yine de safe)
        head_json = GetHead(df.head(10)).get_head()
        return jsonify({'status': 'success', 'head': head_json}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Veri okuma hatası: {str(e)}'}), 400
    
@upload_blueprint.route('/get-columns-api', methods=['POST'])
def get_columns_api():
    try:
        # JSON içindeki sample alanını al
        data = request.get_json()
        if not data or 'sample' not in data:
            return jsonify({'status': 'error', 'message': 'sample verisi eksik'}), 400
        
        sample_text = data['sample']
        
        # CSV içeriğini DataFrame'e çevir
        from io import StringIO
        sample_io = StringIO(sample_text)
        df = pd.read_csv(sample_io)

        # Sütunları çıkar
        from python_scripts.getColumns import GetColumns
        columns = GetColumns(df).get_columns()
        return jsonify({'status': 'success', 'columns': columns}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Veri okuma hatası: {str(e)}'}), 400

def analyze_data_background(filepath, project_name, file_name, app_instance):
    """
    Arkaplanda veri analizini yapar ve sonuçları WebSocket ile gönderir
    Büyük dosyalar için optimize edilmiş versiyonu
    """
    with app_instance.app_context():
        try:
            # Analiz başlatıldı bilgisi
            socketio.emit('data_analysis_status', {
                'status': 'started',
                'message': 'Veri analizi başlatıldı...',
                'project_name': project_name,
                'file_name': file_name
            })
            
            # Dosyanın varlığını kontrol et
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Dosya bulunamadı: {filepath}")
            
            # Dosya boyutunu kontrol et (GB limitli)
            file_size_bytes = os.path.getsize(filepath)
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            # 100MB üzerindeki dosyalar için özel optimizasyon
            if file_size_mb > 100:
                app_instance.logger.info(f'Büyük dosya tespit edildi: {file_size_mb:.2f}MB')
                return analyze_large_file(filepath, project_name, file_name, file_size_mb, app_instance)
            
            # Dosyayı okuma kontrolü - chunksize ile optimize et
            try:
                # İlk birkaç satırı kontrol et
                sample_df = pd.read_csv(filepath, nrows=100)
                if sample_df.empty:
                    raise ValueError("Dosya boş veya geçersiz")
                
                # Küçük dosyalar için full load
                df = pd.read_csv(filepath)
                
            except pd.errors.EmptyDataError:
                raise ValueError("CSV dosyası boş")
            except pd.errors.ParserError as e:
                raise ValueError(f"CSV formatı hatalı: {str(e)}")
            except Exception as e:
                raise ValueError(f"Dosya okuma hatası: {str(e)}")
            
            # Güvenlik kontrolleri
            if len(df.columns) == 0:
                raise ValueError("Dosyada sütun bulunamadı")
            
            if len(df) == 0:
                raise ValueError("Dosyada veri bulunamadı")
                
            # WebSocket ile analiz başladığını bildir
            socketio.emit('data_analysis_status', {
                'status': 'progress',
                'message': 'Dosya başarıyla yüklendi...',
                'step': 1,
                'total_steps': 6
            })
            
            # 1. Temel bilgiler - hızlı hesaplama
            socketio.emit('data_analysis_status', {
                'status': 'progress',
                'message': 'Temel bilgiler hesaplanıyor...',
                'step': 2,
                'total_steps': 6
            })
            
            total_rows = len(df)
            total_columns = len(df.columns)
            missing_values = df.isnull().sum().sum()
            
            # 2. Sütun tipleri analizi
            socketio.emit('data_analysis_status', {
                'status': 'progress',
                'message': 'Sütun tipleri analiz ediliyor...',
                'step': 3,
                'total_steps': 6
            })
            
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
            
            # 3. İstatistiksel özellikler - sadece ilk 5 numeric sütun
            socketio.emit('data_analysis_status', {
                'status': 'progress',
                'message': 'İstatistiksel özellikler hesaplanıyor...',
                'step': 4,
                'total_steps': 6
            })
            
            if len(numeric_columns) > 0:
                # Sadece ilk 5 numeric sütunu kullan - performans için
                numeric_subset = numeric_columns[:5]
                numeric_df = df[numeric_subset]
                
                # Güvenli istatistik hesaplama - NaN ve infinity kontrolü
                import numpy as np
                
                try:
                    # Aşırı değerleri filtrele (outlier removal)
                    filtered_df = numeric_df.copy()
                    
                    # Her sütun için ayrı ayrı outlier temizleme
                    for col in numeric_subset:
                        Q1 = filtered_df[col].quantile(0.25)
                        Q3 = filtered_df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        
                        # IQR metoduyla outlier sınırları
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        
                        # Outlier'ları filtrele
                        filtered_df[col] = filtered_df[col].where(
                            (filtered_df[col] >= lower_bound) & (filtered_df[col] <= upper_bound)
                        )
                    
                    # Temizlenmiş veriden istatistik hesapla
                    skewness_values = filtered_df.skew().replace([np.inf, -np.inf], np.nan).fillna(0)
                    avg_skewness = float(skewness_values.mean()) if not skewness_values.empty else 0.0
                    
                    std_values = filtered_df.std().replace([np.inf, -np.inf], np.nan).fillna(0)
                    # Çok yüksek std değerlerini sınırla (1 milyon üzeri)
                    std_values = std_values.where(std_values < 1000000, 0)
                    avg_std = float(std_values.mean()) if not std_values.empty else 0.0
                    
                    var_values = filtered_df.var().replace([np.inf, -np.inf], np.nan).fillna(0)
                    # Çok yüksek varyans değerlerini sınırla
                    var_values = var_values.where(var_values < 1000000000, 0)
                    avg_variance = float(var_values.mean()) if not var_values.empty else 0.0
                    
                    # Korelasyon matrisi sadece küçük datasette
                    if total_rows < 10000 and len(numeric_subset) <= 3:
                        correlation_matrix = numeric_df.corr()
                        correlation_matrix = correlation_matrix.fillna(0)
                    else:
                        correlation_matrix = None
                        
                except Exception as stat_error:
                    app_instance.logger.warning(f'İstatistik hesaplama hatası: {str(stat_error)}')
                    avg_skewness = avg_std = avg_variance = 0.0
                    correlation_matrix = None
            else:
                avg_skewness = 0.0
                avg_std = 0.0
                avg_variance = 0.0
                correlation_matrix = None
            
            # 4. Sayısal sütunların detaylı istatistikleri - sadece ilk 3 sütun
            socketio.emit('data_analysis_status', {
                'status': 'progress',
                'message': 'Detaylı sütun istatistikleri hesaplanıyor...',
                'step': 5,
                'total_steps': 6
            })
            
            column_statistics = []
            for col in numeric_columns[:3]:  # Sadece ilk 3 sayısal sütun - performans
                try:
                    import numpy as np
                    
                    col_data = df[col].dropna()
                    
                    if len(col_data) == 0:
                        continue
                    
                    # Outlier temizleme ile istatistik hesaplama
                    try:
                        # IQR metoduyla outlier temizleme
                        Q1 = col_data.quantile(0.25)
                        Q3 = col_data.quantile(0.75)
                        IQR = Q3 - Q1
                        
                        # Outlier sınırları
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        
                        # Outlier'ları filtrele
                        clean_data = col_data[(col_data >= lower_bound) & (col_data <= upper_bound)]
                        
                        # Temizlenmiş veriden istatistik hesapla
                        if len(clean_data) > 0:
                            stats = clean_data.describe()
                            col_stats = {
                                'column_name': str(col),
                                'mean': float(stats['mean']) if np.isfinite(stats['mean']) else 0.0,
                                'std': float(stats['std']) if np.isfinite(stats['std']) and stats['std'] < 1000000 else 0.0,
                                'min': float(stats['min']) if np.isfinite(stats['min']) else 0.0,
                                'max': float(stats['max']) if np.isfinite(stats['max']) else 0.0,
                                'median': float(stats['50%']) if np.isfinite(stats['50%']) else 0.0,
                                'outliers_removed': int(len(col_data) - len(clean_data))
                            }
                        else:
                            # Eğer tüm veri outlier ise, original veriyi kullan ama std'yi sınırla
                            stats = col_data.describe()
                            col_stats = {
                                'column_name': str(col),
                                'mean': float(stats['mean']) if np.isfinite(stats['mean']) else 0.0,
                                'std': min(float(stats['std']), 1000000) if np.isfinite(stats['std']) else 0.0,
                                'min': float(stats['min']) if np.isfinite(stats['min']) else 0.0,
                                'max': float(stats['max']) if np.isfinite(stats['max']) else 0.0,
                                'median': float(stats['50%']) if np.isfinite(stats['50%']) else 0.0,
                                'outliers_removed': 0,
                                'note': 'Tüm veriler aşırı değer olarak tespit edildi'
                            }
                        column_statistics.append(col_stats)
                    except Exception as desc_error:
                        app_instance.logger.warning(f'Describe hatası {col}: {str(desc_error)}')
                        continue
                        
                except Exception as e:
                    app_instance.logger.warning(f'Sütun {col} için istatistik hesaplanamadı: {str(e)}')
                    continue
            
            # 5. Veri önizleme - sadece ilk 5 satır
            socketio.emit('data_analysis_status', {
                'status': 'progress',
                'message': 'Veri önizlemesi hazırlanıyor...',
                'step': 6,
                'total_steps': 6
            })
            
            # Sadece ilk 5 satır ve ilk 10 sütun - performans
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
                        record[str(col)] = str(value)[:100]  # String'leri kısalt
                preview_records.append(record)
            
            data_preview = {
                'columns': [str(col) for col in preview_df.columns],
                'data': preview_records,
                'total_rows': int(total_rows),
                'note': 'İlk 5 satır ve 10 sütun gösteriliyor' if total_columns > 10 else None
            }
            
            # Sonuçları topla
            analysis_results = {
                'basic_info': {
                    'total_rows': int(total_rows),
                    'total_columns': int(total_columns),
                    'file_size': round(float(file_size_mb), 2),
                    'missing_values': int(missing_values),
                    'numeric_columns_count': int(len(numeric_columns)),
                    'categorical_columns_count': int(len(categorical_columns))
                },
                'statistical_features': {
                    'avg_skewness': round(float(avg_skewness), 3) if avg_skewness and np.isfinite(avg_skewness) else 0.0,
                    'avg_std': round(float(avg_std), 2) if avg_std and np.isfinite(avg_std) else 0.0,
                    'avg_variance': round(float(avg_variance), 2) if avg_variance and np.isfinite(avg_variance) else 0.0,
                    'correlation_status': str('Hesaplanmış' if correlation_matrix is not None else 'Performans için atlandı'),
                    'note': 'Büyük dosyalarda ilk 5 sütun analiz edilir'
                },
                'column_statistics': column_statistics,
                'data_preview': data_preview,
                'project_name': str(project_name),
                'file_name': str(file_name)
            }
            
            socketio.emit('data_analysis_complete', {
                'status': 'completed',
                'message': 'Veri analizi tamamlandı!',
                'results': analysis_results
            })
            
        except FileNotFoundError as e:
            error_msg = f'Dosya bulunamadı: {str(e)}'
            app_instance.logger.error(f'File not found error in analysis: {error_msg}')
            socketio.emit('data_analysis_error', {
                'status': 'error',
                'message': error_msg,
                'error_type': 'file_not_found',
                'project_name': project_name,
                'file_name': file_name
            })
            
        except ValueError as e:
            error_msg = f'Veri formatı hatası: {str(e)}'
            app_instance.logger.error(f'Data format error in analysis: {error_msg}')
            socketio.emit('data_analysis_error', {
                'status': 'error',
                'message': error_msg,
                'error_type': 'data_format',
                'project_name': project_name,
                'file_name': file_name
            })
            
        except MemoryError as e:
            error_msg = 'Dosya çok büyük. Lütfen daha küçük bir dosya yükleyin.'
            app_instance.logger.error(f'Memory error in analysis: {str(e)}')
            socketio.emit('data_analysis_error', {
                'status': 'error',
                'message': error_msg,
                'error_type': 'memory_error',
                'project_name': project_name,
                'file_name': file_name
            })
            
        except Exception as e:
            error_msg = f'Beklenmeyen hata: {str(e)}'
            app_instance.logger.error(f'Unexpected error in analysis: {str(e)}')
            socketio.emit('data_analysis_error', {
                'status': 'error',
                'message': error_msg,
                'error_type': 'general',
                'project_name': project_name,
                'file_name': file_name
            })


def analyze_large_file(filepath, project_name, file_name, file_size_mb, app_instance):
    """
    Büyük dosyalar için optimize edilmiş analiz fonksiyonu
    """
    import numpy as np
    
    try:
        socketio.emit('data_analysis_status', {
            'status': 'progress',
            'message': f'Büyük dosya ({file_size_mb:.1f}MB) tespit edildi. Optimize analiz başlatılıyor...',
            'step': 1,
            'total_steps': 4
        })
        
        # 1. Sadece sample okuma - ilk 10000 satır
        sample_size = min(10000, 50000)  # Max 50k satır
        df_sample = pd.read_csv(filepath, nrows=sample_size)
        
        socketio.emit('data_analysis_status', {
            'status': 'progress',
            'message': f'Örnek veri ({sample_size} satır) yüklendi...',
            'step': 2,
            'total_steps': 4
        })
        
        # 2. Temel bilgiler - dosya boyutundan tahmin
        total_rows_estimate = int((file_size_mb * 1024 * 1024) / (len(df_sample) * 100))  # Rough estimation
        total_columns = len(df_sample.columns)
        
        numeric_columns = df_sample.select_dtypes(include=['number']).columns.tolist()
        categorical_columns = df_sample.select_dtypes(include=['object']).columns.tolist()
        
        socketio.emit('data_analysis_status', {
            'status': 'progress',
            'message': 'Hızlı istatistik hesaplaması...',
            'step': 3,
            'total_steps': 4
        })
        
        # 3. Basit istatistikler - sadece sample'dan (outlier temizleme ile)
        column_statistics = []
        if len(numeric_columns) > 0:
            for col in numeric_columns[:2]:  # Sadece ilk 2 sütun
                try:
                    col_data = df_sample[col].dropna()
                    if len(col_data) > 10:  # En az 10 veri noktası olsun
                        # Outlier temizleme
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
                                'std': min(float(stats['std']), 1000000) if np.isfinite(stats['std']) else 0.0,
                                'min': float(stats['min']) if np.isfinite(stats['min']) else 0.0,
                                'max': float(stats['max']) if np.isfinite(stats['max']) else 0.0,
                                'median': float(stats['50%']) if np.isfinite(stats['50%']) else 0.0,
                                'note': 'Büyük dosya sample + outlier temizleme'
                            }
                            column_statistics.append(col_stats)
                except:
                    continue
        
        # 4. Minimal preview
        preview_df = df_sample.head(3).iloc[:, :5]  # 3 satır, 5 sütun
        
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
                    record[str(col)] = str(value)[:50]  # Kısa string
            preview_records.append(record)
        
        socketio.emit('data_analysis_status', {
            'status': 'progress',
            'message': 'Büyük dosya analizi tamamlanıyor...',
            'step': 4,
            'total_steps': 4
        })
        
        analysis_results = {
            'basic_info': {
                'total_rows': total_rows_estimate,
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
                'total_rows': total_rows_estimate,
                'note': 'Büyük dosya - ilk 3 satır ve 5 sütun'
            },
            'project_name': str(project_name),
            'file_name': str(file_name)
        }
        
        socketio.emit('data_analysis_complete', {
            'status': 'completed',
            'message': f'Büyük dosya analizi tamamlandı! ({file_size_mb:.1f}MB)',
            'results': analysis_results
        })
        
    except Exception as e:
        app_instance.logger.error(f'Large file analysis error: {str(e)}')
        socketio.emit('data_analysis_error', {
            'status': 'error',
            'message': f'Büyük dosya analiz hatası: {str(e)}',
            'error_type': 'large_file_error',
            'project_name': project_name,
            'file_name': file_name
        })