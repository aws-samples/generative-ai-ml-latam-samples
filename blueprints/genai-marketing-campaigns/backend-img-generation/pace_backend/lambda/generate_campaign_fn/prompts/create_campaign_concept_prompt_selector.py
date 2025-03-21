# Copyright 2024 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: LicenseRef-.amazon.com.-AmznSL-1.0
# Licensed under the Amazon Software License  http://aws.amazon.com/asl/

from langchain.chains.prompt_selector import ConditionalPromptSelector

from .prompts import NOVA_AD_CONCEPT_SYSTEM_PROMPT_EN, NOVA_AD_CONCEPT_USER_PROMPT_EN

from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, \
    AIMessagePromptTemplate

from typing import Callable

# AMAZON NOVA PROMPT TEMPLATES

# English Prompts

NOVA_AD_CONCEPT_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(NOVA_AD_CONCEPT_SYSTEM_PROMPT_EN, validate_template=True, input_variables=["json_schema"]),
    HumanMessagePromptTemplate.from_template(NOVA_AD_CONCEPT_USER_PROMPT_EN, input_variables=["campaign_desc"], validate_template=True),
])


def is_en(language: str) -> bool:
    return "en" == language


def is_nova(model_id: str) -> bool:
    return "nova" in model_id


def is_en_nova(language: str) -> Callable[[str], bool]:
    return lambda model_id: is_en(language) and is_nova(model_id)


def get_ad_concept_prompt_selector(lang: str) -> ConditionalPromptSelector:
    return ConditionalPromptSelector(
        default_prompt=NOVA_AD_CONCEPT_PROMPT_TEMPLATE_EN,
        conditionals=[
        ]
    )

