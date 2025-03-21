from pydantic import BaseModel, Field
from typing import List

class ImageDescription(BaseModel):
    """The description of an image"""
    description: str = Field(description="The description of the image")
    elements: List[str] = Field(description="A list of the elements present in the image")