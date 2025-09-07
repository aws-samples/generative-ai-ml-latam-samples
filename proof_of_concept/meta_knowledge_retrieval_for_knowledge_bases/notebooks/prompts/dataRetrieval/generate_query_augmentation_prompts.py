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

from langchain.chains.prompt_selector import ConditionalPromptSelector

from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, \
    AIMessagePromptTemplate

from .kb_query_augmentation_prompts import QUERY_AUGMENTATION_SYSTEM_PROMPT_EN, QUERY_AUGMENTATION_USER_PROMPT_EN, STRUCTURED_QUESTIONS_GENERATION_EN

from typing import Callable

def is_en(language: str) -> bool:
    return "en" == language

def is_nova(model_id: str) -> bool:
    return "nova" in model_id

# QA generation prompt

NOVA_QUERY_AUGMENTATION_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        QUERY_AUGMENTATION_SYSTEM_PROMPT_EN,
        input_variables=["role", "mk_summary"],
        validate_template=True
    ),
    HumanMessagePromptTemplate.from_template(
        QUERY_AUGMENTATION_USER_PROMPT_EN,
        input_variables=["user_query"],
        validate_template=True
    ),
])

def get_query_augmentation_prompt_selector(lang: str) -> ConditionalPromptSelector:
    return ConditionalPromptSelector(
        default_prompt=NOVA_QUERY_AUGMENTATION_PROMPT_TEMPLATE_EN,
        conditionals=[
        ]
    )

# QA structured output prompt

NOVA_QUESTIONS_STRUCTURED_OUTPUT_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
    HumanMessagePromptTemplate.from_template(
        STRUCTURED_QUESTIONS_GENERATION_EN,
        input_variables=["question_list"],
        validate_template=True
    ),
])

def get_structured_questions_prompt_selector(lang: str) -> ConditionalPromptSelector:
    return ConditionalPromptSelector(
        default_prompt=NOVA_QUESTIONS_STRUCTURED_OUTPUT_PROMPT_TEMPLATE_EN,
        conditionals=[
        ]
    )