import os
from website_provider import WebsiteContentProvider
from models import Asset, InputAssets

class BlogPostProvider(WebsiteContentProvider):
    def __init__(self, config):
        self.config = config

    def get_content_from_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def get_content(self) -> InputAssets:
        content_list = []

        for asset in self.config['input_assets']:
            if self.is_url(asset):
                try:
                    content = self.get_content_from_url(asset)
                except Exception as e:
                    print(f"Failed to fetch or parse {asset}: {e}")
                    continue
            else:
                if not os.path.isfile(asset):
                    print(f"File {asset} not found. Skipping.")
                    continue
                content = self.get_content_from_file(asset)

            content_list.append(Asset(content=content))

        input_assets = InputAssets(assets=content_list)

        print(f"Loaded {len(input_assets.assets)} blog posts..")

        return input_assets