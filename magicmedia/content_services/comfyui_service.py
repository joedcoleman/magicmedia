import json
import requests
from PIL import Image
from websocket import create_connection
import os
import io
import sys
import uuid
import time

class ComfyConnector:
    def __init__(self):
        self.server_address = "http://localhost:8188"
        self.client_id = str(uuid.uuid4())
        self.ws_address = f"ws://localhost:8188/ws?clientId={self.client_id}"
        self.ws = None

    def connect_websocket(self):
        print("Connecting to WebSocket...")
        self.ws = create_connection(self.ws_address)  # Use create_connection from websocket-client library
        print("Connected to WebSocket.")

    def _prepare_payload(self, workflow_path, input_assets):
        input_assets = [asset.content for asset in input_assets.assets]

        def replace_load_image(node):
            nonlocal input_assets_index
            if isinstance(node, dict):
                for key, value in node.items():
                    if key == "class_type" and value == "LoadImage" and input_assets_index < len(input_assets):
                        filename = os.path.basename(input_assets[input_assets_index])
                        node["inputs"]["image"] = filename
                        input_assets_index += 1
                    else:
                        replace_load_image(value)
            elif isinstance(node, list):
                for item in node:
                    replace_load_image(item)

        print("Loading workflow!")
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)

        input_assets_index = 0
        replace_load_image(workflow)

        return workflow

    def generate_images(self, workflow_path, input_assets):
        try:
            if self.ws is None or not self.ws.connected:
                self.connect_websocket()

            payload = self._prepare_payload(workflow_path, input_assets)
            prompt_response = self.queue_prompt(payload)
            prompt_id = prompt_response['prompt_id']
            print(f"Prompt queued with ID: {prompt_id}")

            is_complete = False
            while not is_complete:
                print("Checking generation status...")
                history = self.get_history(prompt_id)
                if prompt_id in history:
                    history_output = history[prompt_id]
                    # Check if the history indicates completion, adjust the key as necessary
                    if 'outputs' in history_output:
                        is_complete = True
                if not is_complete:
                    print("Generation not complete, waiting 2 seconds...")
                    time.sleep(2)  # Wait for 2 seconds before checking again

            print("Image generation complete, fetching images...")
            # After confirming completion, fetch images
            address = self.find_output_node(payload)
            filenames = eval(f"history_output['outputs']{address}")['images']
            output_dir = 'output'  # Replace with the path to your input directory
            for img_info in filenames:
                filename = img_info['filename']
                subfolder = img_info['subfolder']
                folder_type = img_info['type']
                image_data = self.get_image(filename, subfolder, folder_type)
                image_file = io.BytesIO(image_data)
                image = Image.open(image_file)
                image_path = os.path.join(output_dir, filename)
                image.save(image_path)
            print(f"Images saved in {output_dir}")

        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            line_no = exc_traceback.tb_lineno
            error_message = f'Unhandled error at line {line_no}: {str(e)}'
            print("generate_images - ", error_message)
        finally:
            if self.ws and self.ws.connected:
                print("Closing WebSocket connection...")
                self.ws.close()
                print("WebSocket connection closed.")

    def queue_prompt(self, prompt):
        p = {"prompt": prompt}
        data = json.dumps(p).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        req = requests.post(f"{self.server_address}/prompt", data=data, headers=headers)
        return json.loads(req.content)

    def get_history(self, prompt_id):
        response = requests.get(f"{self.server_address}/history/{prompt_id}")
        print(response.json())
        return response.json()

    def get_image(self, filename, subfolder, folder_type):
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        response = requests.get(f"{self.server_address}/view", params=data)
        return response.content

    def upload_image(self, filepath, subfolder=None, folder_type=None, overwrite=True):
        try: 
            url = f"{self.server_address}/upload/image"
            files = {'image': open(filepath, 'rb')}
            data = {'overwrite': str(overwrite).lower()}
            if subfolder:
                data['subfolder'] = subfolder
            if folder_type:
                data['type'] = folder_type
            response = requests.post(url, files=files, data=data)
            return response.json()
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            line_no = exc_traceback.tb_lineno
            error_message = f'upload_image - Unhandled error at line {line_no}: {str(e)}'
            print(error_message)
            return None

    @staticmethod
    def find_output_node(json_object):
        for key, value in json_object.items():
            if isinstance(value, dict):
                if value.get("class_type") == "SaveImage":
                    return f"['{key}']"
                result = ComfyConnector.find_output_node(value)
                if result:
                    return result
        return None