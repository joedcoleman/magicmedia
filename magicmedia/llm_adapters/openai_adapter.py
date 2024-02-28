import os
from dotenv import load_dotenv
from openai import OpenAI

from .llm_interface import LLMInterface
from ..models import *

class OpenAIAdapter(LLMInterface):
    def __init__(self, model='gpt-4-turbo-preview'):
        self.model = model

    def _construct_messages(self, context):
        messages = []

        for message in context:
            if isinstance(message, SystemMessage):
                messages.append({"role": "system", "content": message.content})
            elif isinstance(message, UserMessage):
                messages.append({"role": "user", "content": message.content})
            elif isinstance(message, AssistantMessage):
                messages.append({"role": "assistant", "content": message.content})

        return messages

    def generate_content(self, context):
        load_dotenv()
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        messages = self._construct_messages(context)

        print("Generating content with OpenAI..")

        completion = client.chat.completions.create(
            messages=messages,
            model=self.model,
        )

        generated_content = completion.choices[0].message.content

        print(f"\n\n{completion.usage}\n\n")

        return generated_content