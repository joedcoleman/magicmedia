from ..content_services.comfyui_service import ComfyConnector
from .content_generator_interface import ContentGeneratorInterface

class ImageVariationGenerator(ContentGeneratorInterface):

    def __init__(self, config, input_content):
        self.config = config
        self.input_content = input_content
        self.workflow_path = "content_services/workflows/image_variation.json"

    def generate_content(self):
        comfy = ComfyConnector()

        # Upload input images to comfy
        input_assets = [asset.content for asset in self.input_content.assets]
        
        for image_path in input_assets:
            comfy.upload_image(image_path)

        # Run the workflow
        output = comfy.generate_images(self.workflow_path, self.input_content)

        return output