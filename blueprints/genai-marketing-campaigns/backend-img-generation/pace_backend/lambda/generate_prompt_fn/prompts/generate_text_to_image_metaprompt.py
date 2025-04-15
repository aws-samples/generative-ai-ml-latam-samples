# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Amazon Software License (the "License"). You may not
# use this file except in compliance with the License. A copy of the
# License is located at:
# http://aws.amazon.com/asl/
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
# See the License for the specific language governing permissions and
# limitations under the License.

from langchain.chains.prompt_selector import ConditionalPromptSelector

from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, \
    AIMessagePromptTemplate
from langchain_core.prompts.few_shot import FewShotChatMessagePromptTemplate

from .examples.img_prompts_examples import examples_eng
from .prompts import NOVA_META_PROMPTING_IMG_SYSTEM_PROMPT_EN, NOVA_META_PROMPTING_IMG_USER_PROMPT_WITH_REFERENCES_EN, NOVA_META_PROMPTING_IMG_USER_PROMPT_WITHOUT_REFERENCES_EN

from typing import Callable

txt_to_img_examples_prompt_template_en = ChatPromptTemplate.from_messages(
    [
        HumanMessagePromptTemplate.from_template("<meta-prompt-example>{txt-img-prompt}</meta-prompt-example>", input_variables=["txt-img-prompt"], validate_template=True)
    ]
)

few_shot_meta_prompt_eng = FewShotChatMessagePromptTemplate(
    example_prompt=txt_to_img_examples_prompt_template_en,
    examples=examples_eng,
)

NOVA_META_PROMPT_GENERATION_WITH_REFERENCES_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(NOVA_META_PROMPTING_IMG_SYSTEM_PROMPT_EN, validate_template=True, input_variables=["json_schema"]),
    few_shot_meta_prompt_eng,
    HumanMessagePromptTemplate.from_template(NOVA_META_PROMPTING_IMG_USER_PROMPT_WITH_REFERENCES_EN, input_variables=["text"], validate_template=True),
])

NOVA_META_PROMPT_GENERATION_WITHOUT_REFERENCES_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(NOVA_META_PROMPTING_IMG_SYSTEM_PROMPT_EN, validate_template=True, input_variables=["json_schema"]),
    few_shot_meta_prompt_eng,
    HumanMessagePromptTemplate.from_template(NOVA_META_PROMPTING_IMG_USER_PROMPT_WITHOUT_REFERENCES_EN, input_variables=["text"], validate_template=True),
])


def is_en(language: str) -> bool:
    return "en" == language


def is_nova(model_id: str) -> bool:
    return "nova" in model_id

def is_en_with_references(language: str, with_references:bool):
    return is_en(language) and with_references

def is_en_nova_with_references(language: str, with_references: bool) -> Callable[[str], bool]:
    return lambda model_id: is_en_with_references(language, with_references) and is_nova(model_id)


def get_meta_prompt_prompt_selector(lang: str, is_with_references: bool) -> ConditionalPromptSelector:
    return ConditionalPromptSelector(
        default_prompt=NOVA_META_PROMPT_GENERATION_WITHOUT_REFERENCES_PROMPT_TEMPLATE_EN,
        conditionals=[
            (is_en_nova_with_references(lang, is_with_references), NOVA_META_PROMPT_GENERATION_WITH_REFERENCES_PROMPT_TEMPLATE_EN),
            (is_en_nova_with_references(lang, not is_with_references),
             NOVA_META_PROMPT_GENERATION_WITHOUT_REFERENCES_PROMPT_TEMPLATE_EN)
        ]
    )