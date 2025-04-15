# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import re
import logging
import json

import boto3

from langchain_aws import ChatBedrockConverse

from prompts.generate_text_to_image_metaprompt import get_meta_prompt_prompt_selector
from structured_output.meta_prompt import MetaPrompt
import langchain_core

lambda_response = {
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": True,
    },
    "body": {},
}

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL"))

langchain_core.globals.set_debug(True)

CAMPAIGN_TABLE_NAME = os.getenv("CAMPAIGN_TABLE_NAME")
REGION = os.getenv("REGION")
MODEL_ID = os.getenv("MODEL_ID")

campaignTable = boto3.resource("dynamodb").Table(CAMPAIGN_TABLE_NAME)

def generate_text_to_image_meta_prompt(campaign_details, with_reference_images=False, reference_image_descriptions=[]):

    meta_prompt_llm = ChatBedrockConverse(
        model=MODEL_ID,
        temperature=0.7,
        max_tokens=500,
        # other params...
    )

    if with_reference_images:
        logger.debug("meta prompt with reference images")

        LLM_GENERATE_META_PROMPT_WITH_REFERENCES_PROMPT_SELECTOR = get_meta_prompt_prompt_selector(lang="en", is_with_references=True)

        img_gen_meta_prompt = LLM_GENERATE_META_PROMPT_WITH_REFERENCES_PROMPT_SELECTOR.get_prompt(MODEL_ID)
        structured_meta_prompt= meta_prompt_llm.with_structured_output(MetaPrompt)

        structured_meta_prompt_with_img_reference = img_gen_meta_prompt | structured_meta_prompt

        reference_image_descriptions = [f"<reference_image_description>{img_desc}</reference_image_description>" for img_desc in reference_image_descriptions]

        img_meta_prompt = structured_meta_prompt_with_img_reference.invoke(
            {
                "text": campaign_details,
                "related_images": "\n".join(reference_image_descriptions),
                "json_schema": MetaPrompt.model_json_schema()
            }
        )

    else:
        logger.debug("meta prompt without reference images")

        LLM_GENERATE_META_PROMPT_WITHOUT_REFERENCES_PROMPT_SELECTOR = get_meta_prompt_prompt_selector(lang="en", is_with_references=False)

        img_gen_meta_prompt = LLM_GENERATE_META_PROMPT_WITHOUT_REFERENCES_PROMPT_SELECTOR.get_prompt(MODEL_ID)
        structured_meta_prompt= meta_prompt_llm.with_structured_output(MetaPrompt)

        structured_meta_prompt_with_img_reference = img_gen_meta_prompt | structured_meta_prompt

        img_meta_prompt = structured_meta_prompt_with_img_reference.invoke(
            {
                "text": campaign_details,
                "json_schema": MetaPrompt.model_json_schema()
            }
        )


    return img_meta_prompt


def handler(event, context):

    #Validate event

    logger.debug("Received event: ")
    logger.debug(event)

    method = event["httpMethod"]
    uid = event["uid"]

    if method != "POST":

        lambda_response["statusCode"] = 400
        lambda_response["body"]["message"] = "Bad Request. Malformed URL"

        return lambda_response

    body = event["body"]
    logger.debug("the body")
    logger.debug(body)

    #Read dynamo table and obtain current campaign
    logger.debug("Querying DynamoDB")
    ans = campaignTable.get_item(Key={'id':uid})
    logger.debug("Loaded item")
    logger.debug(ans)

    if 'Item' in ans:
        campaign = ans["Item"]

        #campaign_json = pace_utils.dynamodb_to_json(ans['Item'])
        #campaign = json.loads(campaign_json)
    else:
        logger.error("No id: " + uid)

        lambda_response["statusCode"] = 400
        lambda_response["body"]["message"] = "Campaign not found"

        return lambda_response

    # Get attributes for campaign
    campaign_description = campaign['campaign_description']
    similar_imgs = campaign['image_references']
    selected_references = body['references']

    if not campaign_description:

        lambda_response["statusCode"] = 400
        lambda_response["body"]["message"] = "No campaign description"

        return lambda_response

    logger.debug("Campaign description")
    logger.debug(campaign_description)
    logger.debug("similar imgs")
    logger.debug(similar_imgs)
    logger.debug("selected img references")
    logger.debug(selected_references)

    #Generate meta-prompt
    if len(selected_references) != 0:

        #Get the selected image descriptions from the references
        descriptions_list = [img['description'] for img in similar_imgs if img['url'] in selected_references]

        #Use selected references for the generation of the new images
        img_meta_prompt = generate_text_to_image_meta_prompt(campaign_details=campaign_description, with_reference_images=True, reference_image_descriptions=descriptions_list)
    else:

        #Do not use references for the generation of the new images
        img_meta_prompt =  generate_text_to_image_meta_prompt(campaign_details=campaign_description, with_reference_images=False)

    logger.debug("Generated meta prompt")
    logger.debug(img_meta_prompt)

    #Update dynamo table
    if not "image_prompt" in campaign:
      campaign["image_prompt"] = {}
    campaign["image_prompt"]["ai_prompt"]= img_meta_prompt.prompt
    campaign["image_prompt"]["ai_reasoning"] = img_meta_prompt.reasoning
    campaignTable.put_item(Item=campaign)

    lambda_response["statusCode"] = 200
    lambda_response["body"] = json.dumps({
        "ai_image_prompt": img_meta_prompt.prompt,
        "ai_reasoning":img_meta_prompt.reasoning
    })

    return lambda_response
