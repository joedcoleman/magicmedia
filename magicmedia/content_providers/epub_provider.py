import ebooklib
from ebooklib import epub
from models import Asset

class EpubProvider:
    def __init__(self, file_path):
        self.file_path = file_path

    def get_content_from_file(self, chapters):
        if chapters:
            assets = []
            content = self.get_chapters()
            for chapter in content:
                assets.append(Asset(content=chapter))
            return assets
        else:
            book = epub.read_epub(self.file_path)
            text = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    text.append(item.get_content().decode('utf-8'))
            content = " ".join(text)
            return Asset(content=content)

    def get_chapters(self):
        book = epub.read_epub(self.file_path)
        chapters = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                chapters.append(item.get_content().decode('utf-8'))
        return chapters

    def get_content(self, chapters=False):
        content = self.get_content_from_file(chapters)

        return content