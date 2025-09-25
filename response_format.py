from pydantic import BaseModel, Field
from typing import List

class Response(BaseModel):
    message: str = Field(description="The assistant's reply message")
    base_random_keys: List[str] = Field(description="List of the assistant's base random keys")
    member_random_keys: List[str] = Field(description="List of the assistant's member random keys")