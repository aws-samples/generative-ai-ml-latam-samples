# MIT No Attribution
#
# Copyright 2025 Amazon Web Services
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from pydantic import BaseModel, Field
from typing import List
from datetime import date

class DocumentMetadata(BaseModel):
    """The metadata of a document processed by an LLM"""
    main_category: str = Field(description="The main category of the document")
    secondary_categories: List[str] = Field(description="A list of other categories in which the document can be classified")
    document_references: List[str] = Field(description="A list of documents referenced in the document")
    technologies: List[str] = Field(description="A list of technologies mentioned in the document")
    evaluations: List[str] = Field(description="A list of evaluations or metrics mentioned in the document")
    document_date: str = Field("", description="The date of the document")
    document_version: str = Field("", description="The version of the document")