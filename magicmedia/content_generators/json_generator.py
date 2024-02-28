from ..models import SystemMessage, UserMessage
from .content_generator_interface import ContentGeneratorInterface
from ..post_processors.json_post_processor import JsonPostProcessor

class JsonGenerator(ContentGeneratorInterface):

    def __init__(self, input_content, llm, instructions):
        self.input_content = input_content
        self.llm = llm
        self.instructions = instructions

    def generate_content(self):
        context = [SystemMessage(content=self.instructions), UserMessage(content=self.input_content)]
        output_content = self.llm.generate_content(context=context)

        post_processor = JsonPostProcessor()
        validated_json = post_processor.process(output_content)

        return validated_json