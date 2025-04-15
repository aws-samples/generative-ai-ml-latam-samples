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
