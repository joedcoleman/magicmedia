from ..models import Asset
import requests
from urllib.parse import urlparse
import html2text


class WebsiteContentProvider:
    def __init__(self, url):
        self.url = url

    def is_url(self, path):
        try:
            result = urlparse(path)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def get_content(self):
        response = requests.get(self.url)
        response.raise_for_status()  # Raise an error for bad requests

        html = response.content
        h = html2text.HTML2Text()
        h.ignore_links = True  # Optionally ignore links
        text = h.handle(html.decode('utf-8'))  

        return Asset(content=text)