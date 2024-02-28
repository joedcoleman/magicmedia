from ..prompts import EBOOK_PROMPT
from .content_generator_interface import ContentGeneratorInterface
from ..post_processors.ebook_post_processor import EBookPostProcessor

class EBookGenerator(ContentGeneratorInterface):

    def __init__(self, config, input_content):
        self.config = config
        self.input_content = input_content

    def _construct_messages(self):
        messages = []

        system_message = EBOOK_PROMPT

        if self.config.get("llm_instructions", None):
            system_message += f"\n\nPlease take into account these additional instructions from the user: {self.config['llm_instructions']}"

        messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": self.input_content.combine_content()})

        return messages

    def generate_content(self):
        LLMAdapter = get_llm_adapter(self.config)
        llm = LLMAdapter(self.config)

        output_content = llm.generate_content(messages=self._construct_messages())
        processed_content = EBookPostProcessor.process(output_content, 'ebook.pdf')

        return processed_content