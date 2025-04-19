import pandas as pd
def get_file_info(file_path):
    """Yüklenen dosyadan sütun ve örnek satır bilgilerini al"""
    try:
        extension = file_path.split('.')[-1].lower()
        if extension == 'csv':
            df = pd.read_csv(file_path)
        elif extension == 'xlsx':
            df = pd.read_excel(file_path)
        elif extension == 'json':
            df = pd.read_json(file_path)
        elif extension == 'xml':
            df = pd.read_xml(file_path)
            
        return {
            'columns': df.columns.tolist(),
            'sample_data': df.head(5).to_dict('records'),
            'row_count': len(df),
            'column_types': df.dtypes.astype(str).to_dict()
        }
    except Exception as e:
        return {'error': str(e)}
