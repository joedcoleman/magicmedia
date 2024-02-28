from ..models import Asset

class TextFileProvider:
    def __init__(self, file_path):
        self.file_path = file_path

    def get_content(self):
        with open(self.file_path, 'rb') as file:
            return Asset(content=file.read())