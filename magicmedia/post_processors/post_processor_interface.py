from abc import ABC, abstractmethod

class PostProcessorInterface(ABC):
    @abstractmethod
    def process(self, content):
        pass