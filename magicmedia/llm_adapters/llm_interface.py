from abc import ABC, abstractmethod

class LLMInterface(ABC):
    @abstractmethod
    def generate_content(self, input_content, prompt):
        """
        Generates new content using the LLM.
        """
        pass