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


class QuestionGenerationOutput(BaseModel):
    """Format for question generation task"""
    summary: str = Field(description="The summary of the document")
    text_relevancy_assessment: str = Field(
        description="The assessment of whether the text is relevant or not for the task")
    is_text_relevant: bool = Field(description="True if the text is relevant for the task, False otherwise")
    questions: List[str] = Field(default=[], description="A list of questions")


class DocumentQuestions(BaseModel):
    """Extract a set of questions from a document"""
    is_text_relevant: bool = Field(description="A boolean value stating the relevancy of the text to the assigned task")
    questions: List[str] = Field([],
                                 description="A set of questions from the document. Only the question is to be extracted, no preambles, numbers or labels are needed")
    summary: str = Field("", description="The summary section of the document")


class QuestionEvaluation(BaseModel):
    """A set of evaluations for a question"""
    question: str = Field(description="The question being evaluated")
    reasoning: str = Field(description="The assesment of the question regarding the evaluation framework")
    is_simple: int = Field(0,
                           description="1 if the question is standalone, that is it has no dependencies to other questions, 0 otherwise")
    is_standalone: int = Field(0,
                               description="1 if the question is specific and simple, 0 if the question can be broken into simpler questions")
    aligned_to_gold_standard: int = Field(0,
                                          description="1 if the question is similar in form and sintax to the gold standard, 0 otherwise")


class QEvals(BaseModel):
    """Evaluations for a question set"""
    question_evals: List[QuestionEvaluation] = Field(description="A list of question evaluations")

