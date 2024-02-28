import PyPDF2
from ..models import Asset

class PdfProvider:
    def __init__(self, file_path):
        self.file_path = file_path

    def get_content_from_file(self):
        with open(self.file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = []
            for page in range(len(reader.pages)):
                text.append(reader.pages[page].extract_text())
            return " ".join(text)

    def get_content(self):
        content = self.get_content_from_file()
        return Asset(content=content)