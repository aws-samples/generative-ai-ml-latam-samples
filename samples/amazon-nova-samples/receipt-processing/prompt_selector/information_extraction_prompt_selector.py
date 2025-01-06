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

import os

from langchain.chains.prompt_selector import ConditionalPromptSelector

from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, \
    AIMessagePromptTemplate
from langchain_core.prompts.few_shot import FewShotChatMessagePromptTemplate

from .prompts import (
    CLAUDE_INFORMATION_EXTRACTION_SYSTEM_PROMPT_ES,
    CLAUDE_INFORMATION_EXTRACTION_USER_PROMPT_ES,
    CLAUDE_INFORMATION_EXTRACTION_WITH_EXAMPLES_SYSTEM_PROMPT_ES,
    CLAUDE_INFORMATION_EXTRACTION_WITH_EXAMPLES_USER_PROMPT_ES,
    CLAUDE_INFORMATION_EXTRACTION_SYSTEM_PROMPT_EN,
    CLAUDE_INFORMATION_EXTRACTION_USER_PROMPT_EN,
    CLAUDE_INFORMATION_EXTRACTION_WITH_EXAMPLES_SYSTEM_PROMPT_EN,
    CLAUDE_INFORMATION_EXTRACTION_WITH_EXAMPLES_USER_PROMPT_EN,
    NOVA_INFORMATION_EXTRACTION_SYSTEM_PROMPT_ES,
    NOVA_INFORMATION_EXTRACTION_USER_PROMPT_ES,
    NOVA_INFORMATION_EXTRACTION_WITH_EXAMPLES_SYSTEM_PROMPT_ES,
    NOVA_INFORMATION_EXTRACTION_WITH_EXAMPLES_USER_PROMPT_ES,
    NOVA_INFORMATION_EXTRACTION_SYSTEM_PROMPT_EN,
    NOVA_INFORMATION_EXTRACTION_USER_PROMPT_EN,
    NOVA_INFORMATION_EXTRACTION_WITH_EXAMPLES_SYSTEM_PROMPT_EN,
    NOVA_INFORMATION_EXTRACTION_WITH_EXAMPLES_USER_PROMPT_EN
)

from .langchain_example_selector import CharterReportsExampleSelector

from typing import Callable


def is_es(language: str) -> bool:
    return "es" == language


def is_en(language: str) -> bool:
    return "en" == language


def is_claude(model_id: str) -> bool:
    return "claude" in model_id


def is_nova(model_id: str) -> bool:
    return "nova" in model_id


def is_es_claude(language: str) -> Callable[[str], bool]:
    return lambda model_id: is_es(language) and is_claude(model_id)


def is_en_claude(language: str) -> Callable[[str], bool]:
    return lambda model_id: is_en(language) and is_claude(model_id)


def is_es_nova(language: str) -> Callable[[str], bool]:
    return lambda model_id: is_es(language) and is_nova(model_id)


def is_en_nova(language: str) -> Callable[[str], bool]:
    return lambda model_id: is_en(language) and is_nova(model_id)


def get_information_extraction_prompt_selector(lang: str, example_type: str=None) -> ConditionalPromptSelector:
    dir_path = os.path.dirname(os.path.realpath(__file__))

    if example_type:

        # Prompt template for the examples
        examples_prompt_template = ChatPromptTemplate.from_messages(
            [
                HumanMessagePromptTemplate.from_template("<text>{text}</text>", input_variables=["text"],
                                                         validate_template=True),
                AIMessagePromptTemplate.from_template("<extracted_information>{extraction}<extracted_information>",
                                                      input_variables=["extraction"], validate_template=True)
            ]
        )

        # Example selector
        charter_reports_example_selector = CharterReportsExampleSelector(
            examples_location=os.path.join(dir_path, "examples", lang, example_type))

        # Few-shot prompt with prompt selector.
        few_shot_chat_prompt_template = FewShotChatMessagePromptTemplate(
            input_variables=[
                "n_examples"
            ],
            # The input variables select the values to pass to the example_selector
            example_selector=charter_reports_example_selector,
            # Define how each example will be formatted.
            example_prompt=examples_prompt_template,
        )

        # Prompts by language

        #Anthropic
        CLAUDE_INFORMATION_EXTRACTION_WITH_EXAMPLES_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(CLAUDE_INFORMATION_EXTRACTION_WITH_EXAMPLES_SYSTEM_PROMPT_EN, input_variables=["n_examples", "json_schema"],
                                                      validate_template=True),
            few_shot_chat_prompt_template,
            HumanMessagePromptTemplate.from_template(CLAUDE_INFORMATION_EXTRACTION_WITH_EXAMPLES_USER_PROMPT_EN, input_variables=[],
                                                     validate_template=True),
        ])

        CLAUDE_INFORMATION_EXTRACTION_WITH_EXAMPLES_PROMPT_TEMPLATE_ES = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(CLAUDE_INFORMATION_EXTRACTION_WITH_EXAMPLES_SYSTEM_PROMPT_ES, input_variables=["n_examples", "json_schema"],
                                                      validate_template=True),
            few_shot_chat_prompt_template,
            HumanMessagePromptTemplate.from_template(CLAUDE_INFORMATION_EXTRACTION_WITH_EXAMPLES_USER_PROMPT_ES,
                                                     input_variables=[], validate_template=True),
        ])

        #Nova
        NOVA_INFORMATION_EXTRACTION_WITH_EXAMPLES_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(NOVA_INFORMATION_EXTRACTION_WITH_EXAMPLES_SYSTEM_PROMPT_EN, input_variables=["n_examples", "json_schema"],
                                                      validate_template=True),
            few_shot_chat_prompt_template,
            HumanMessagePromptTemplate.from_template(NOVA_INFORMATION_EXTRACTION_WITH_EXAMPLES_USER_PROMPT_EN, input_variables=[],
                                                     validate_template=True),
        ])

        NOVA_INFORMATION_EXTRACTION_WITH_EXAMPLES_PROMPT_TEMPLATE_ES = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(NOVA_INFORMATION_EXTRACTION_WITH_EXAMPLES_SYSTEM_PROMPT_ES, input_variables=["n_examples", "json_schema"],
                                                      validate_template=True),
            few_shot_chat_prompt_template,
            HumanMessagePromptTemplate.from_template(NOVA_INFORMATION_EXTRACTION_WITH_EXAMPLES_USER_PROMPT_ES,
                                                     input_variables=[], validate_template=True),
        ])

        return ConditionalPromptSelector(
            default_prompt=CLAUDE_INFORMATION_EXTRACTION_WITH_EXAMPLES_PROMPT_TEMPLATE_EN,
            conditionals=[
                (is_es_claude(lang), CLAUDE_INFORMATION_EXTRACTION_WITH_EXAMPLES_PROMPT_TEMPLATE_ES),
                (is_es_nova(lang), NOVA_INFORMATION_EXTRACTION_WITH_EXAMPLES_PROMPT_TEMPLATE_ES),
                (is_en_nova(lang), NOVA_INFORMATION_EXTRACTION_WITH_EXAMPLES_PROMPT_TEMPLATE_EN)
            ]
        )
    else:
        
        # Prompts by language

        #Anthropic
        CLAUDE_INFORMATION_EXTRACTION_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(CLAUDE_INFORMATION_EXTRACTION_SYSTEM_PROMPT_EN, input_variables=["json_schema"], validate_template=True),
            HumanMessagePromptTemplate.from_template(CLAUDE_INFORMATION_EXTRACTION_USER_PROMPT_EN, input_variables=[], validate_template=True),
            HumanMessagePromptTemplate.from_template([{'image_url': {'url': '{image_path}', 'detail': '{detail_parameter}'}}],
                                         input_variables=['image_path', 'detail_parameter'], validate_template=True)
        ])

        CLAUDE_INFORMATION_EXTRACTION_PROMPT_TEMPLATE_ES = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(CLAUDE_INFORMATION_EXTRACTION_SYSTEM_PROMPT_ES, input_variables=["json_schema"], validate_template=True),
            HumanMessagePromptTemplate.from_template(CLAUDE_INFORMATION_EXTRACTION_USER_PROMPT_ES, input_variables=[], validate_template=True),
            HumanMessagePromptTemplate.from_template([{'image_url': {'url': '{image_path}', 'detail': '{detail_parameter}'}}],
                                         input_variables=['image_path', 'detail_parameter'], validate_template=True)
        ])

        #Nova
        NOVA_INFORMATION_EXTRACTION_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(NOVA_INFORMATION_EXTRACTION_SYSTEM_PROMPT_EN, input_variables=["json_schema"],
                                                      validate_template=True),
            HumanMessagePromptTemplate.from_template(NOVA_INFORMATION_EXTRACTION_USER_PROMPT_EN, input_variables=[],
                                                     validate_template=True),
            HumanMessagePromptTemplate.from_template([{'image_url': {'url': '{image_path}', 'detail': '{detail_parameter}'}}],
                                         input_variables=['image_path', 'detail_parameter'], validate_template=True)
        ])

        NOVA_INFORMATION_EXTRACTION_PROMPT_TEMPLATE_ES = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(NOVA_INFORMATION_EXTRACTION_SYSTEM_PROMPT_ES, input_variables=["json_schema"],
                                                      validate_template=True),
            HumanMessagePromptTemplate.from_template(NOVA_INFORMATION_EXTRACTION_USER_PROMPT_ES,
                                                     input_variables=[], validate_template=True),
            HumanMessagePromptTemplate.from_template([{'image_url': {'url': '{image_path}', 'detail': '{detail_parameter}'}}],
                                                     input_variables=['image_path', 'detail_parameter'], validate_template=True)
        ])

        return ConditionalPromptSelector(
            default_prompt=CLAUDE_INFORMATION_EXTRACTION_PROMPT_TEMPLATE_EN,
            conditionals=[
                (is_es_claude(lang), CLAUDE_INFORMATION_EXTRACTION_PROMPT_TEMPLATE_ES),
                (is_en_nova(lang), NOVA_INFORMATION_EXTRACTION_PROMPT_TEMPLATE_EN),
                (is_es_nova(lang), NOVA_INFORMATION_EXTRACTION_PROMPT_TEMPLATE_ES),
            ]
        )