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
import boto3
import json
import decimal

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL"))

CAMPAIGN_TABLE_NAME = os.getenv("CAMPAIGN_TABLE_NAME")
HISTORIC_TABLE_NAME = os.getenv("HISTORIC_TABLE_NAME")
campaignTable = boto3.resource("dynamodb").Table(CAMPAIGN_TABLE_NAME)

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super().default(o)

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
    logger.debug("Received event: " + json.dumps(event))
    method = event["httpMethod"]
    path = event["path"]
    pathParts = path.split('/')

    if method != "GET" or len(pathParts) < 2 or pathParts[1] != "campaigns":

        lambda_response["statusCode"] = 400
        lambda_response["body"]["message"] = "Bad Request. Malformed URL"

        return lambda_response

    uid = None
    if len(pathParts) > 2:
      uid = pathParts[2]

    result = None
    if uid == None:
      ans = campaignTable.scan()
      result = ans['Items']
      while "LastEvaluatedKey" in ans.keys() and ans['LastEvaluatedKey'] != []:
        ans = campaignTable.scan(ExclusiveStartKey = ans['LastEvaluatedKey'])
        result.extend(ans['Items'])

    else:
      ans = campaignTable.get_item(Key={'id':uid})
      if 'Item' in ans:
        result = ans['Item']
      else:
        result = []

    lambda_response["statusCode"] = 200
    lambda_response["body"] = json.dumps(result, cls=DecimalEncoder)

    return lambda_response
