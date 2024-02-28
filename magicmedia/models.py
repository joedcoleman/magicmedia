from pydantic import BaseModel, Field
from typing import List, Literal

class Asset(BaseModel):
    content: str

class InputAssets(BaseModel):
    assets: List[Asset]

    def combine_content(self) -> str:
        """Combine content from all assets into a single string."""
        combined_content = ""
        for asset in self.assets:
            combined_content += asset.content + "\n\n"
        return combined_content.strip()

class Message(BaseModel):
    content: str
    file_ids: List[str] = None

class UserMessage(Message):
    role: Literal["user"] = "user"

class AssistantMessage(Message):
    role: Literal["assistant"] = "assistant"

class SystemMessage(Message):
    role: Literal["system"] = "system"