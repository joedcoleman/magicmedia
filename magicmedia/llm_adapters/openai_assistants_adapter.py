from .llm_interface import LLMInterface
from ..models import UserMessage, AssistantMessage, SystemMessage
from openai import OpenAI
import time

class OpenAIAssistantsAdapter(LLMInterface):
    def __init__(self, assistant_id, file_ids=None):
        self.client = OpenAI()
        self.assistant_id = assistant_id
        self.file_ids = file_ids

    def generate_content(self, context):
        print(f"Generating content with OpenAI Assistant: {self.assistant_id}")

        # Create the thread
        thread = self.client.beta.threads.create()

        # Add messages to the thread
        for message in context:
            if isinstance(message, UserMessage):
                params = {"thread_id": thread.id, "role": "user", "content": message.content}
                if self.file_ids:
                    params["file_ids"] = self.file_ids
            elif isinstance(message, AssistantMessage):
                params = {"thread_id": thread.id, "role": "assistant", "content": message.content}
            else:
                continue
        
            self.client.beta.threads.messages.create(**params)

        # Run the thread
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant_id,
        )

        # Check the Run status until it's completed
        while True:
            run_status = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == 'completed':
                print(run_status.model_dump())
                break
            time.sleep(3)

        # Display the Assistant's Response
        messages = self.client.beta.threads.messages.list(thread_id=thread.id)
        messages_list = list(messages)
        
        # Then, reverse the list to ensure correct chronological order
        messages_list.reverse()

        print(messages_list)

        generated_content = ''
        for message in messages_list:
            if message.role == "assistant":
                generated_content = message.content[0].text.value

        return generated_content
