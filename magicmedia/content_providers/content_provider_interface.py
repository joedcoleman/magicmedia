from abc import ABC, abstractmethod

class ContentProviderInterface(ABC):
    @abstractmethod
    def get_content(self):
        """
        Retrieves content from a specified source.
        
        Returns:
            content (str or list): The raw content to be processed.
        """
        pass