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

import boto3
import json
import functools
import secrets
import datetime

from status_info_layer.StatusEnum import QuestionStatusEnum

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger

from botocore.exceptions import ClientError

logger = Logger()

bucket_name = os.environ.get("DOCUMENTS_BUCKET_NAME")
sns_topic_arn = os.environ.get("TEXTRACT_SNS_TOPIC_ARN")
sns_role_arn = os.environ.get("TEXTRACT_SNS_ROLE_ARN")
dynamo_db_table_name = os.environ.get("JOBS_DYNAMO_DB_TABLE_NAME")

client_textract = boto3.client('textract')
table = boto3.resource("dynamodb").Table(dynamo_db_table_name)

# TODO: use aws_lambda_powertools.event_handler import APIGatewayRestResolver and CORSConfig to avoid having to
#  know about API GW response formats
def _format_response(handler):
    @functools.wraps(handler)
    def wrapper(event, context):
        lambda_response = handler(event, context)

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
            response["body"] = json.dumps({
                "job_id": lambda_response["job_id"],
                "status": lambda_response["job_status"]
            })
        else:
            response["body"] = json.dumps({
                "job_id": lambda_response["job_id"],
                "status": lambda_response["job_status"],
                "message": "Error processing document"
            })

        return response

    return wrapper


@_format_response
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, _context: LambdaContext):
    """
    Lambda function to start an asynchronous text extraction job in Textract
    @param event:
    @param context:
    @return:
    """

    logger.info(f"Received event: {event}")

    event_body = json.loads(event["body"])

    print("The payload")
    print(type(event_body))
    print(event_body)

    print("The sns topic")
    print(sns_topic_arn)

    print("The IAM role")
    print(sns_role_arn)

    # Execute Textract Job
    try:
        document_file_key = event_body["key"]
        main_job_id = event_body["main_job_id"]
        document_file_name = event_body["metadata"]["filename"]
        document_key = event_body["metadata"]["doc_key"]

        logger.info("Processing document %s", document_file_name)

        request_token = secrets.token_urlsafe(16)

        logger.info(document_file_key)
        logger.info(main_job_id)
        logger.info(document_file_name)
        logger.info(document_key)

        # Start Async text detection
        response = client_textract.start_document_text_detection(
            JobTag=document_key,
            DocumentLocation={
                "S3Object": {"Bucket": bucket_name, "Name": document_file_key}
            },
            NotificationChannel={
                "SNSTopicArn": sns_topic_arn,
                "RoleArn": sns_role_arn,
            },
            ClientRequestToken=request_token,
        )
        job_id = response["JobId"]
        logger.info(
            "Started text detection job %s on %s.", job_id, document_file_key
        )
    except ClientError:
        logger.warning("Couldn't detect text in document.")
        raise

    #time.sleep(2) # Sleep for two seconds before sending request to validate status

    # Validate Job is executing
    try:
        response = client_textract.get_document_text_detection(JobId=job_id)
        job_status = response["JobStatus"]
        logger.info("Job %s status is %s.", job_id, job_status)
    except ClientError:
        logger.warning("Couldn't get text detection job %s.", job_id)

        table.put_item(
            Item={
                "job_id": job_id,
                "main_job_id": main_job_id,
                "timestamp": int(datetime.datetime.now().timestamp()),
                "document_filekey": document_file_key,
                "document_key": document_key,
                "document_name": document_file_name,
                "status": QuestionStatusEnum.ERROR.name,
                "questions": json.dumps([])
            }
        )

        raise

    # Store in DB
    try:
        table.put_item(
            Item={
                "job_id": job_id,
                "main_job_id": main_job_id,
                "document_filekey": document_file_key,
                "timestamp": int(datetime.datetime.now().timestamp()),
                "document_key": document_key,
                "document_name": document_file_name,
                "status": QuestionStatusEnum.TEXT_EXTRACTION.name,
                "questions": json.dumps([])
            }
        )
    except Exception as e:
        logger.warning("Error while updating DynamoDB table for job_id {}".format(job_id))
        raise

    else:
        return {"job_id": job_id, "statusCode": 200, "job_status": job_status}


