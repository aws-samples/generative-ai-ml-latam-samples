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

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL"))

CAMPAIGN_TABLE_NAME = os.getenv("CAMPAIGN_TABLE_NAME")
HISTORIC_TABLE_NAME = os.getenv("HISTORIC_TABLE_NAME")
campaignTable = boto3.resource("dynamodb").Table(CAMPAIGN_TABLE_NAME)


def handler(event, context):
    logger.debug("Received event: " + json.dumps(event))
    method = event["httpMethod"]
    path = event["path"]
    pathParts = path.split('/')

    if method != "DELETE" or len(pathParts) != 3 or pathParts[1] != "campaigns" :
        lambda_response["statusCode"] = 400
        lambda_response["body"]["message"] = "Bad Request. Malformed URL"

        return lambda_response

    uid = pathParts[2]
    campaignTable.delete_item(Key={"id":uid})
    result = {}

    lambda_response["statusCode"] = 200
    lambda_response["body"] = json.dumps(result)

    return lambda_response
