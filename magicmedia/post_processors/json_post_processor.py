import json
from json_repair import repair_json
from .post_processor_interface import PostProcessorInterface

class JsonPostProcessor(PostProcessorInterface):
    def process(self, content):
        try:
            repaired_json_string = repair_json(content)
            json_content = json.loads(repaired_json_string)
            return json_content
        except json.JSONDecodeError as e:
            error_details = {
                "error": "Invalid JSON syntax",
                "message": e.msg,
                "lineno": e.lineno,
                "colno": e.colno
            }
            self._save_invalid_content(content)
            return error_details

    def _save_invalid_content(self, content):
        with open('output/invalid_json.txt', 'w') as f:
            f.write(content)