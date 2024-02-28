from .post_processor_interface import PostProcessorInterface
from pathlib import Path
from openai import OpenAI

class AudiobookPostProcessor(PostProcessorInterface):
    def __init__(self, model="tts-1", voice="shimmer"):
        self.client = OpenAI()
        self.model = model
        self.voice = voice

    def process(self, content, output_file_path):
        # Ensure the output_file_path is a Path object
        speech_file_path = Path('output/' + output_file_path)

        print("Generating audiobook using OpenAI TTS..")

        # Generate the speech audio using OpenAI's TTS
        response = self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=content
        )

        # Save the audio file to the specified path
        response.stream_to_file(speech_file_path)

        # Return the path to the saved audio file
        return f"Audiobook saved to: {output_file_path}"
