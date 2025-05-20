import os
class Project:
    project_json = {
        "project_name": None,
        "file_name": None,
        "extension": None,
        "option": []
    }
prn = ""

def allowed_file(filename):
    if '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    valid_extensions = ['csv', 'xlsx', 'xml', 'json']
    return extension in valid_extensions

def check_colsandrows(file):
    """
    Check columns and rows of the uploaded file.
    Returns a tuple of (column_names, row_count) or None if there's an error.
    """
    try:
        _, ext = os.path.splitext(file.filename)
        extension = ext[1:].lower() if ext else ""
        
        if extension == 'csv':
            import pandas as pd
            df = pd.read_csv(file)
            return list(df.columns), len(df)
            
        elif extension in ['xlsx', 'xls']:
            import pandas as pd
            df = pd.read_excel(file)
            return list(df.columns), len(df)
            
        elif extension == 'json':
            import json
            import pandas as pd
            data = json.load(file)
            if isinstance(data, list):
                df = pd.DataFrame(data)
                return list(df.columns), len(df)
            elif isinstance(data, dict):
                # If it's a dictionary, try to convert to DataFrame
                df = pd.DataFrame([data])
                return list(df.columns), len(df)
            else:
                return None
                
        elif extension == 'xml':
            import xml.etree.ElementTree as ET
            import pandas as pd
            tree = ET.parse(file)
            root = tree.getroot()
            
            # Convert XML to list of dictionaries
            data = []
            for child in root:
                row = {}
                for subchild in child:
                    row[subchild.tag] = subchild.text
                data.append(row)
            
            if data:
                df = pd.DataFrame(data)
                return list(df.columns), len(df)
            return None
            
        else:
            return None
            
    except Exception as e:
        print(f"Error checking columns and rows: {str(e)}")
        return None
