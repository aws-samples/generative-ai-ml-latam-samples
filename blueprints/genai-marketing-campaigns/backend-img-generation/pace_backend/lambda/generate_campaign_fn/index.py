# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import logging
import traceback
import uuid
import json

import boto3

from langchain_aws import ChatBedrockConverse

from prompts.create_campaign_concept_prompt_selector import get_ad_concept_prompt_selector
from structured_output.ad_concept import AdConcept


template = {
   "id": "", #<uuid/cuid/guid>
   "name": "", #Campaign name
   "campaign_description": "", #The campaign's description
   "campaign_concept": "", #The concept of the campaign
   "visual_concept": "", #The visual concept of the campaign
   "image_description": "", #The description of the campaign
   "objective": "", # Campaign objective
   "node": "", #Campaign node
   "results": 0, #Campaign results (to maximize). Zero when created
}

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

LLM_AD_CONCEPT_PROMPT_SELECTOR = get_ad_concept_prompt_selector("en")

MODEL_ID = os.getenv("MODEL_ID")
CAMPAIGN_TABLE_NAME = os.getenv("CAMPAIGN_TABLE_NAME")
HISTORIC_TABLE_NAME = os.getenv("HISTORIC_TABLE_NAME")
campaignTable = boto3.resource("dynamodb").Table(CAMPAIGN_TABLE_NAME)

def generate_campaign(campaign_description):
    """Given a campaign description, create a campaign concept using LLMs"""

    ad_concept_llm = ChatBedrockConverse(
        model=MODEL_ID,
        temperature=1,
        max_tokens=500,
        # other params...
    )

    llm_ad_concept_prompt_template = LLM_AD_CONCEPT_PROMPT_SELECTOR.get_prompt(MODEL_ID)
    structured_claude_ad_concept = ad_concept_llm.with_structured_output(AdConcept)
    structured_ad_concept_llm = llm_ad_concept_prompt_template | structured_claude_ad_concept

    ad_concept = structured_ad_concept_llm.invoke({"campaign_desc": campaign_description, "json_schema": AdConcept.model_json_schema()})

    return ad_concept


def handler(event, context):

    #Validate event
    logger.debug("Received event: " + json.dumps(event))
    method = event["httpMethod"]
    path = event["path"]
    pathParts = path.split('/')

    logger.debug(pathParts)
    logger.debug(method)
    logger.debug(method != "POST")
    logger.debug(len(pathParts) != 2)
    logger.debug(pathParts[1] != "campaigns")

    if method != "POST" or len(pathParts) != 2 or pathParts[1] != "campaigns":

        lambda_response["statusCode"] = 400
        lambda_response["body"]["message"] = "Bad Request. Malformed URL"

        return lambda_response

    logger.debug("Generating campaign")

    #Generate new unique id
    while True:
        uid = str(uuid.uuid4())
        resp = campaignTable.get_item(Key={"id": uid})
        if not "Item" in resp.keys():
            break

    template["id"] = uid

    logger.debug("the body")
    logger.debug(event["body"])

    body = json.loads(event["body"])

    logger.debug("the body")
    logger.debug(body)

    try:
        #Create campaign concept with GenAI
        campaign_concept = generate_campaign(body["campaign_description"])
    except Exception as e:

        logger.debug("Unable to generate campaign concept with LLM")
        logger.debug(traceback.print_exc())

        lambda_response["statusCode"] = 400
        lambda_response["body"]["message"] = "Unable to generate campaign concept with LLM"

        return lambda_response

    logger.debug("the campaign concept")
    logger.debug(campaign_concept)

    template["name"] = body["name"]
    template["campaign_description"] = body["campaign_description"]
    template["campaign_concept"] = campaign_concept.campaign_concept
    template["visual_concept"] = campaign_concept.visual_concept
    template["image_description"] = campaign_concept.image_description
    template["objective"] = body["objective"].lower()
    template["node"] = body["node"].lower()

    resp = campaignTable.put_item(Item=template)

    answer = {"id" :uid,
              "name": template["name"],
              "campaign_description": template["campaign_description"],
              "objective": template["objective"],
              "node": template["node"],
              }

    lambda_response["statusCode"] = 200
    lambda_response["body"] = json.dumps(answer)

    return lambda_response
