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
import uuid
import datetime

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger

from botocore.exceptions import ClientError

from status_info_layer.StatusEnum import ComplianceReportStatusEnum

logger = Logger()

TABLE_NAME = os.getenv("JOBS_DYNAMO_DB_TABLE_NAME")
table = boto3.resource("dynamodb").Table(TABLE_NAME)

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
            "body": json.dumps({
                "job_id": lambda_response["job_id"],
                "job_status": lambda_response["job_status"],
            })
        }

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
    logger.info(f"Received event: {event}")

    event_body = json.loads(event["body"])

    print("The payload")
    print(type(event_body))
    print(event_body)

    job_id = uuid.uuid4().hex[:12]

    # Insert job into the dynamodb table
    try:
        table.put_item(
            Item={
                "job_id": str(job_id),
                "analysis_name": event_body["analysis_name"],
                "workload": event_body["workload"],
                "country": event_body["country"],
                "industry": event_body["industry"],
                "timestamp": int(datetime.datetime.now().timestamp()),
                "gold_standard_questions": json.dumps(event_body["reference_questions"]),
                "status": ComplianceReportStatusEnum.AWAITING.name,
            }
        )
    except Exception as e:
        logger.warning("Error while updating DynamoDB table for job_id {}".format(job_id))
        raise

    else:
        return {"job_id": job_id, "statusCode": 200, "job_status": ComplianceReportStatusEnum.AWAITING.name}



