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

import json
import os
import logging
import re
import functools
import boto3

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger

from botocore.exceptions import ClientError

logger = Logger()

TABLE_NAME = os.getenv("JOBS_DYNAMO_DB_TABLE_NAME")
table = boto3.resource("dynamodb").Table(TABLE_NAME)

GET_TABLE_ITEMS_PATTERN = re.compile("(/[a-zA-Z0-9-]*)*/jobs/query")

# TODO: use aws_lambda_powertools.event_handler import APIGatewayRestResolver and CORSConfig to avoid having to
#  know about API GW response formats
def _format_response(handler):
    @functools.wraps(handler)
    def wrapper(event, context):
        lambda_response = handler(event, context)

        logger.info(lambda_response)

        response = {
            "statusCode": lambda_response["statusCode"],
            "isBase64Encoded": False,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": "",
        }

        logger.info(lambda_response)

        if lambda_response["statusCode"] == 200:

            items = []

            for item in lambda_response["items"]:
                item_response = {
                    "document_name": item["document_name"],
                    "document_key": item["document_key"],
                    "document_filekey": item["document_filekey"],
                    "job_id": item["job_id"],
                    "status": item["status"],
                    "timestamp": int(item.get("timestamp", 0))
                }

                items.append(item_response)

            response["body"] = json.dumps({
                "items": items,
            })
        else:
            response["body"] = json.dumps({
                "message": "Error retrieving jobs"
            })

        return response

    return wrapper

@_format_response
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, _context: LambdaContext):
    """
    Lambda function to retrieve items from DynamoDB
    @param event: Lambda
    @param context:
    @return:
    """
    logger.info("Starting job")
    logger.info("Received event", event)
    logger.info(event.keys())

    method = event["httpMethod"]
    path = event["path"]

    logger.info(method)
    logger.info(path)

    if method == "GET" and GET_TABLE_ITEMS_PATTERN.match(path):
        return _get_items()
    else:
        return {
            "statusCode": 500,
            "items": "Not implemented"
        }


def _get_items():
    items = table.scan()
    return {
        "statusCode": 200,
        "items": items.get("Items", [])
    }
