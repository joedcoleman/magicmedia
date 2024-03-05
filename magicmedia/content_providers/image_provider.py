import os
import requests
from urllib.parse import urlparse
from PIL import Image
from io import BytesIO
from ..models import Asset, InputAssets
from .content_provider_interface import ContentProviderInterface

class ImageProvider(ContentProviderInterface):
    def __init__(self, config):
        self.config = config
        self.images = []
    
    def is_url(self, path):
        try:
            result = urlparse(path)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def get_image_from_file(self, file_path):
        img = Image.open(file_path)
        self.images.append(img)
        return img

    def get_image_from_url(self, url):
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        self.images.append(img)
        return img

    def get_content(self) -> InputAssets:
        image_list = []
        save_directory = "input"

        for asset in self.config['input_assets']:
            if self.is_url(asset):
                try:
                    image = self.get_image_from_url(asset)
                    image_name = os.path.basename(urlparse(asset).path)
                except Exception as e:
                    print(f"Failed to fetch image {asset}: {e}")
                    continue
            else:
                if not os.path.isfile(asset):
                    print(f"File {asset} not found. Skipping.")
                    continue
                image = self.get_image_from_file(asset)
                image_name = os.path.basename(asset)

            save_path = os.path.join(save_directory, image_name)
            image.save(save_path)

            image_list.append(Asset(content=save_path))

        input_assets = InputAssets(assets=image_list)

        print(f"Loaded {len(input_assets.assets)} images..")

        return input_assets
