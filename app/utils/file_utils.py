import os

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
