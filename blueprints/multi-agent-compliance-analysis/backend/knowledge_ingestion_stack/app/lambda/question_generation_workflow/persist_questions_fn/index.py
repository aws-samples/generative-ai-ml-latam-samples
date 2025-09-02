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

import logging
import os
import json
import time
import traceback

import boto3
import functools

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger

from status_info_layer.StatusEnum import QuestionStatusEnum

logger = Logger()

JOBS_DYNAMODB_TABLE_NAME = os.environ.get("JOBS_DYNAMO_DB_TABLE_NAME")

job_table = boto3.resource("dynamodb").Table(JOBS_DYNAMODB_TABLE_NAME)

# TODO: use aws_lambda_powertools.event_handler import APIGatewayRestResolver and CORSConfig to avoid having to
#  know about API GW response formats
def _format_response(handler):
    @functools.wraps(handler)
    def wrapper(event, context):
        response = handler(event, context)
        return {
            "statusCode": response["statusCode"],
            "job_id": response["job_id"],
            "isBase64Encoded": False,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": response.get("body", ""),
            "error": response.get("error", None)
        }

    return wrapper

@_format_response
@logger.inject_lambda_context(log_event=True)
def handler(event, _context: LambdaContext):
    """
    Lambda function to create multiple perspectives per chunk
    @param event:
    @param context:
    @return:
    """

    logger.info(f"Received event: {event}")

    #Retrieve main job id
    document_job_id = event["job_id"]
    questions = event["questions"]

    logger.info(f"Document ID: {document_job_id}")
    logger.debug(questions)

    # Update job status in DynamoDB table
    try:

        job_table.update_item(
            Key={"job_id": document_job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": QuestionStatusEnum.QUESTION_PERSISTENCE.name},
        )

        job_table.update_item(
            Key={"job_id": document_job_id},
            UpdateExpression="SET #questions = :questions",
            ExpressionAttributeNames={"#questions": "questions"},
            ExpressionAttributeValues={":questions": json.dumps(questions)},
        )

        job_table.update_item(
            Key={"job_id": document_job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": QuestionStatusEnum.SUCCESS.name},
        )

    except Exception as e:

        logger.error(f"Error updating DynamoDB: {e}")
        traceback.print_exc()
        raise (e)

    return {
        "statusCode": 200,
        "job_id": document_job_id,
    }
