# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import logging
import json
import boto3

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL"))

CAMPAIGN_TABLE_NAME = os.getenv("CAMPAIGN_TABLE_NAME")
HISTORIC_TABLE_NAME = os.getenv("HISTORIC_TABLE_NAME")
campaignTable = boto3.resource("dynamodb").Table(CAMPAIGN_TABLE_NAME)

lambda_response = {
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": True,
    },
    "body": {},
}

def handler(event, context):
    logger.debug("Received event", event)
    method = event["httpMethod"]
    path = event["path"]
    pathParts = path.split('/')

    if method != "PUT" or len(pathParts) != 3 or pathParts[1] != "suggestion":

        lambda_response["statusCode"] = 200
        lambda_response["body"]["message"] = "Bad request. Malformed request"

        return lambda_response

    uid = pathParts[-1]

    ans = campaignTable.get_item(Key={'id':uid})
    # Get attributes for campaign

    try:
        body = json.loads(event["body"])
        prompt = body["user_prompt"]
        campaign = ans["Item"]
    except:

        lambda_response["statusCode"] = 200
        lambda_response["body"]["message"] = "Bad request. Malformed request"

        return lambda_response


    answer = {"user_prompt": prompt}

    #Update dynamo table
    if not "image_prompt" in campaign:
      campaign["image_prompt"] = {}
    campaign["image_prompt"]["user_prompt"] = prompt
    campaignTable.put_item(Item=campaign)

    lambda_response["statusCode"] = 200
    lambda_response["body"] = json.dumps(answer)

    return lambda_response
