# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import logging
import base64
import io
import uuid
import tempfile
import json

import boto3
from PIL import Image
import random

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

CAMPAIGN_TABLE_NAME = os.getenv("CAMPAIGN_TABLE_NAME")
campaignTable = boto3.resource("dynamodb").Table(CAMPAIGN_TABLE_NAME)

PROCESSED_BUCKET = os.getenv("PROCESSED_BUCKET")

MODEL_ID = os.getenv("IMG_MODEL_ID")

#s3 = boto3.client("s3")
s3 = boto3.resource("s3")
processed_bucket = s3.Bucket(PROCESSED_BUCKET)

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)

def genImgCanvas(prompt: str):
    """Generate an image from a prompt using Amazon Titan models"""

    negative_prompts = "poorly rendered, poor background details, poorly facial details"

    seed = int(random.randrange(0x0CCD569F))  # nosec B311 not being used for security
    logger.debug("seed = " + str(seed))

    # Create payload
    body = json.dumps(
        {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": prompt,
                "negativeText": negative_prompts   # Optional
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,  # Range: 1 to 5
                "quality": "standard",  # Options: standard or premium
                "height": 720,  # Supported height list in the docs
                "width": 1280,  # Supported width list in the docs
                "cfgScale": 7.5,  # Range: 1.0 (exclusive) to 10.0
                "seed": seed  # Range: 0 to 214783647
            }
        }
    )

    response = bedrock_runtime.invoke_model(
        body=body,
        modelId=MODEL_ID,
        accept="application/json",
        contentType="application/json"
    )
    response_body = json.loads(response.get("body").read())

    base_64_img_str = response_body["images"][0]

    tmpdir = tempfile.mkdtemp()
    image_file = str(uuid.uuid4()) + ".jpg"
    image_path = tmpdir + "/" + image_file
    image_1 = Image.open(io.BytesIO(base64.decodebytes(bytes(base_64_img_str, "utf-8"))))

    # save
    image_1.save(image_path)
    return image_path, image_file

def handler(event, context):
    logger.debug("Received event: " + json.dumps(event))
    method = event["httpMethod"]
    path = event["path"]
    pathParts = path.split('/')

    if method != "POST" or len(pathParts) != 3 or pathParts[1] != "generate_images":

        lambda_response["statusCode"] = 400
        lambda_response["body"]["message"] = "Bad Request. Malformed URL"

        return lambda_response

    uid = pathParts[-1]

    # Get attributes for campaign

    try:
        body = json.loads(event["body"])
        prompt = body["prompt"]
    except:
        lambda_response["statusCode"] = 400
        lambda_response["body"]["message"] = "Bad Request. Bad body"

        return lambda_response

    #Generate an image based on the prompt
    image_path, image_file = genImgCanvas(prompt)

    #Read dynamo table
    ans = campaignTable.get_item(Key={'id':uid})
    if 'Item' in ans:
        campaign = ans['Item']
    else:
        lambda_response["statusCode"] = 500
        lambda_response["body"]["message"] = "Campaign not found"

        return lambda_response

    fileKey = campaign["id"] + "/" + image_file
    processed_bucket.upload_file(image_path,fileKey)

    url = "s3://" + PROCESSED_BUCKET + "/" + fileKey


    #Update dynamo table
    ans = campaignTable.get_item(Key={'id':uid})
    if 'Item' in ans:
        campaign = ans['Item']
    else:
        lambda_response["statusCode"] = 500
        lambda_response["body"]["message"] = "Campaign not found"

        return lambda_response
      
    if not "generated_images" in campaign:
      campaign["generated_images"] = []
    campaign["generated_images"].append({"url":url})
    campaignTable.put_item(Item=campaign)

    lambda_response["statusCode"] = 200
    lambda_response["body"] = json.dumps({"url":url})

    return lambda_response
