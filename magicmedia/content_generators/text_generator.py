from ..models import UserMessage, SystemMessage
from .content_generator_interface import ContentGeneratorInterface

class PlainTextGenerator(ContentGeneratorInterface):

    def __init__(self, input_content, llm, instructions):
        self.input_content = input_content
        self.llm = llm
        self.instructions = instructions

    def generate_content(self):
        context = [SystemMessage(content=self.instructions), UserMessage(content=self.input_content)]
        output_content = self.llm.generate_content(context=context)

        return output_content