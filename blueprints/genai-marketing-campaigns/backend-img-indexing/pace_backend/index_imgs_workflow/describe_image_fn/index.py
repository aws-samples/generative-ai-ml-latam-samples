# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import logging

import boto3
import os
import base64

#from PIL import Image

from langchain_aws import ChatBedrockConverse

from prompts.describe_image_prompt_selector import get_describe_image_prompt_selector
from structured_output.img_description import ImageDescription
import langchain_core

langchain_core.globals.set_debug(True)

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL"))

IMG_BUCKET = os.getenv("IMG_BUCKET")
MODEL_ID = os.getenv("MODEL_ID")

DESCRIBE_IMAGE_PROMPT_SELECTOR = get_describe_image_prompt_selector("en")

# Initialize clients
REGION = boto3.session.Session().region_name

s3_client = boto3.client('s3')

img_desc_llm = ChatBedrockConverse(
    model=MODEL_ID,
    temperature=1,
    max_tokens=500,
    # other params...
)

lambda_response = {
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": True,
    },
    "body": {},
}

"""Describe image using LLM"""
def lambda_handler(event, context):

    try:

        img_key = event['img_key']

        #download image from S3 given bucket name and key
        s3_response = s3_client.get_object(Bucket=IMG_BUCKET, Key=img_key)

        image_bytes = s3_response['Body'].read()

        #transform image to base64
        image_b64 = base64.b64encode(s3_response['Body'].read()).decode('utf8')

        logger.info("image in bytes:\n")
        logger.info(image_bytes)

        logger.info("image in base64:\n")
        logger.info(image_b64)

        # Ask the LLM to describe the image
        describe_image_prompt_template = DESCRIBE_IMAGE_PROMPT_SELECTOR.get_prompt(MODEL_ID)
        structured_img_desc = img_desc_llm.with_structured_output(ImageDescription)

        #Create messages
        human_msg = {
            "role": "user",
            "content": [
                {
                    "text": describe_image_prompt_template.format(json_schema=ImageDescription.model_json_schema())
                }
            ]
        }

        img_message = {
            "role": "user",
            "content": [
                {
                    "image": {
                        "format": 'jpeg',
                        "source": {
                            "bytes": image_bytes
                        }
                    }
                }
            ]
        }

        messages = [human_msg, img_message]

        # Invoke LLM
        img_description = structured_img_desc.invoke(messages)

        lambda_response['statusCode'] = 201
        lambda_response['body']['labels_list'] = img_description.elements
        lambda_response['body']['description'] = img_description.description
        lambda_response['body']['msg'] = 'success'

    except Exception as e:
        logger.error(e)

        lambda_response['statusCode'] = 500
        lambda_response['body']['msg'] = 'Could not describe image'

        raise e

    return lambda_response