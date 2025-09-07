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

from .meta_kb_prompts import NOVA_META_KB_SUMMARY_COLD_START_SYSTEM_PROMPT_EN, NOVA_META_KB_SUMMARY_SYSTEM_PROMPT_EN, NOVA_META_KB_SUMMARY_USER_PROMPT_EN

from typing import Callable

NOVA_CHUNK_SUMMARY_GENERATION_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        NOVA_META_KB_SUMMARY_SYSTEM_PROMPT_EN,
        validate_template=True,
        input_variables=["topic_perspective", "document_types", "users_types"]
    ),
    HumanMessagePromptTemplate.from_template(
        NOVA_META_KB_SUMMARY_USER_PROMPT_EN,
        input_variables=["qa_pairs"],
        validate_template=True
    ),
])

NOVA_SUMMARY_GENERATION_WITH_CONTEXT_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        NOVA_META_KB_SUMMARY_SYSTEM_PROMPT_EN,
        validate_template=True,
        input_variables=["topic_perspective", "document_types", "users_types", "summary"]
    ),
    HumanMessagePromptTemplate.from_template(
        NOVA_META_KB_SUMMARY_USER_PROMPT_EN,
        input_variables=["qa_pairs"],
        validate_template=True
    ),
])

NOVA_SUMMARY_GENERATION_WITHOUT_CONTEXT_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        NOVA_META_KB_SUMMARY_COLD_START_SYSTEM_PROMPT_EN,
        validate_template=True,
        input_variables=["topic_perspective", "document_types", "users_types"]
    ),
    HumanMessagePromptTemplate.from_template(
        NOVA_META_KB_SUMMARY_USER_PROMPT_EN,
        input_variables=["qa_pairs"],
        validate_template=True
    ),
])

def is_en(language: str) -> bool:
    return "en" == language

def is_nova(model_id: str) -> bool:
    return "nova" in model_id

def has_context(with_context: bool) -> bool:
    return with_context

def for_chunks(for_chunks: bool) -> bool:
    return for_chunks

def is_en_nova_with_context(language: str, with_context: bool) -> Callable[[str], bool]:
    return lambda model_id: is_en(language) and is_nova(model_id) and (with_context==True)

def is_en_nova_for_chunks(language: str, for_chunks: bool) -> Callable[[str], bool]:
    return lambda model_id: is_en(language) and is_nova(model_id) and (for_chunks==True)

def get_summary_prompt_selector(lang: str, for_chunks: bool, with_context: bool) -> ConditionalPromptSelector:
    return ConditionalPromptSelector(
        default_prompt=NOVA_SUMMARY_GENERATION_WITHOUT_CONTEXT_PROMPT_TEMPLATE_EN,
        conditionals=[
            (is_en_nova_for_chunks(lang, for_chunks), NOVA_CHUNK_SUMMARY_GENERATION_PROMPT_TEMPLATE_EN),
            (is_en_nova_with_context(lang, with_context), NOVA_SUMMARY_GENERATION_WITH_CONTEXT_PROMPT_TEMPLATE_EN)
        ]
    )