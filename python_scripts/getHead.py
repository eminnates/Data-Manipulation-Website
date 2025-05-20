class GetHead:
    def __init__(self, data):
        self.data = data

    def get_head(self):
        return self.data.head(10).to_json(orient="records")