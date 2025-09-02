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

from .questions_gen_prompts import NOVA_QUESTIONS_GEN_SYSTEM_PROMPT_EN, NOVA_QUESTIONS_GEN_USER_PROMPT_EN, NOVA_QUESTIONS_GEN_USER_PROMPT_WITH_CONTEXT_EN, NOVA_STRUCTURED_QUESTIONS_GENERATION_EN

from typing import Callable

def is_en(language: str) -> bool:
    return "en" == language


def is_nova(model_id: str) -> bool:
    return "nova" in model_id

def is_en_nova(language: str) -> Callable[[str], bool]:
    return lambda model_id: is_en(language) and is_nova(model_id)

############-----------Question generation prompts---------------#############

def is_en_nova_with_feedback(language: str, with_feedback: bool) -> Callable[[str], bool]:
    return lambda model_id: is_en(language) and is_nova(model_id) and with_feedback

NOVA_QUESTIONS_GENERATION_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        NOVA_QUESTIONS_GEN_SYSTEM_PROMPT_EN,
        validate_template=True,
        input_variables=["industry", "country", "workload"],
    ),
    HumanMessagePromptTemplate.from_template(
        NOVA_QUESTIONS_GEN_USER_PROMPT_EN,
        input_variables=["n_questions", "regulation_portion"],
        validate_template=True
    ),
])

NOVA_QUESTIONS_GENERATION_WITH_CONTEXT_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        NOVA_QUESTIONS_GEN_SYSTEM_PROMPT_EN,
        validate_template=True,
        input_variables=["industry", "country", "workload"],
    ),
    HumanMessagePromptTemplate.from_template(
        NOVA_QUESTIONS_GEN_USER_PROMPT_WITH_CONTEXT_EN,
        input_variables=["n_questions", "regulation_portion", "feedback"],
        validate_template=True
    ),
])

def get_questions_prompt_selector(lang: str, with_feedback: bool) -> ConditionalPromptSelector:
    return ConditionalPromptSelector(
        default_prompt=NOVA_QUESTIONS_GENERATION_PROMPT_TEMPLATE_EN,
        conditionals=[
            (is_en_nova_with_feedback(lang, with_feedback), NOVA_QUESTIONS_GENERATION_WITH_CONTEXT_PROMPT_TEMPLATE_EN),
        ]
    )


############-----------Question extraction with structured outputs prompts---------------#############


NOVA_QUESTIONS_EXTRACTION_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
    HumanMessagePromptTemplate.from_template(
        NOVA_STRUCTURED_QUESTIONS_GENERATION_EN,
        input_variables=["questions_text"],
        validate_template=True
    ),
])

def extract_questions_prompt_selector(lang: str) -> ConditionalPromptSelector:
    return ConditionalPromptSelector(
        default_prompt=NOVA_QUESTIONS_EXTRACTION_PROMPT_TEMPLATE_EN,
        conditionals=[
        ]
    )