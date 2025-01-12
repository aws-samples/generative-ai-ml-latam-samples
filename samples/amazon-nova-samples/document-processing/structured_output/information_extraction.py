# MIT No Attribution
#
# Copyright 2024 Amazon Web Services
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

class InformationExtraction(BaseModel):
    """Detalles acerca de la tarea de extraccion de informacion asignada al modelo (LLM)"""
    thinking: str = Field(description="El razonamiento del LLM referente a si puede o no concluir la tarea")
    confidence_level: int = Field(0, description="El grado de confianza que tiene el LLM para realizar la tarea de extraccion de informacion")
    conclusion: bool = Field(False, description="Si el LLM considera que la informacion solicitada puede ser extraida a partir de la entrada presentada")
    extracted_information: str = Field(description="La informacion extraida por el LLM")