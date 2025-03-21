# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import logging
import json
import boto3
from botocore.client import Config
from urllib.parse import urlparse

lambda_response = {
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": True,
    },
    "body": {},
}

REGION = os.getenv("AWS_REGION")

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL"))

s3_client = boto3.client("s3",config=Config(region_name = REGION,signature_version="s3v4"))

duration = 24 * 60 * 60

def handler(event, context):
    logger.debug("Received event: " + json.dumps(event))
    method = event["httpMethod"]
    path = event["path"]
    pathParts = path.split('/')

    if method != "POST" or len(pathParts) != 2 or pathParts[1] != "presign":

        lambda_response["statusCode"] = 400
        lambda_response["body"]["message"] = "Bad Request. Malformed URL"

        return lambda_response

    answer = {}

    try:
        body = json.loads(event["body"])
        s3_path = body["s3Path"]
        parsed = urlparse(s3_path)
        bucket = parsed.netloc
        key = parsed.path[1:]
        presigned = s3_client.generate_presigned_url(
                      ClientMethod="get_object",
                      Params={'Bucket': bucket, 'Key': key},
                      ExpiresIn=duration)
        logger.debug("Bucket: " + bucket + " key: " + key)
        answer["s3Path"] = presigned
        
    except:
        lambda_response["statusCode"] = 400
        lambda_response["body"]["message"] = "Bad Request. Bad body"

        return lambda_response

    lambda_response["statusCode"] = 200
    lambda_response["body"] = json.dumps(answer)

    return lambda_response
