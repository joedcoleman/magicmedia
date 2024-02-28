from abc import ABC, abstractmethod

class ContentGeneratorInterface(ABC):
    @abstractmethod
    def generate_content(self):
        """
        Retrieves content from a specified source.
        
        Returns:
            content (str or list): The raw content to be processed.
        """
        pass