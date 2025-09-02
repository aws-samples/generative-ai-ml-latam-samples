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

from prompt_selector.writer_agent_prompts import WRITER_AGENT_SYSTEM_PROMPT_TEMPLATE, WRITER_AGENT_USER_PROMPT_TEMPLATE

from typing import Callable

WRITER_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        WRITER_AGENT_SYSTEM_PROMPT_TEMPLATE,
        validate_template=True,
        input_variables=["industry", "country", "workload", "section_name"],
    ),
    HumanMessagePromptTemplate.from_template(
        WRITER_AGENT_USER_PROMPT_TEMPLATE,
        input_variables=["qa_set", "section_description", "section_number"],
        validate_template=True
    ),
])

def is_en(language: str) -> bool:
    return "en" == language

def is_nova(model_id: str) -> bool:
    return "nova" in model_id

def is_en_nova(language: str) -> Callable[[str], bool]:
    return lambda model_id: is_en(language) and is_nova(model_id)

def get_writer_prompt_selector(lang: str) -> ConditionalPromptSelector:
    return ConditionalPromptSelector(
        default_prompt=WRITER_PROMPT_TEMPLATE_EN,
        conditionals=[
        ]
    )