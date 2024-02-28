import os
from dotenv import load_dotenv
import google.generativeai as genai

from .llm_interface import LLMInterface
from ..models import *

class GeminiAdapter(LLMInterface):
    def __init__(self, model='gemini-pro'):
        self.model = model
        self.configure_api()

    def configure_api(self):
        load_dotenv()
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

    def _construct_messages(self, context):
        messages = []

        for message in context:
            if isinstance(message, SystemMessage) or isinstance(message, UserMessage):
                if messages and messages[-1]["role"] == "user":
                    # If the last message is a 'user' message, append the content to it
                    messages[-1]["parts"].append(f"\n\n{message.content}")
                else:
                    # Otherwise, create a new 'user' message
                    messages.append({"role": "user", "parts": [message.content]})
            elif isinstance(message, AssistantMessage):
                messages.append({"role": "model", "parts": [message.content]})

        return messages

    def generate_content(self, context):
        generative_model = genai.GenerativeModel(self.model)
        messages = self._construct_messages(context)

        print("Generating content with Gemini..")

        response = generative_model.generate_content(messages)

        generated_content = response.text

        return generated_content