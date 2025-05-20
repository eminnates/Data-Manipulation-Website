import json

class GetColumns:
    def __init__(self, data):
        self.data = data

    def get_columns(self):
        return list(self.data.columns)
