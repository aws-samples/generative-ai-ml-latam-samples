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
import boto3
import functools
import tempfile
from TextractorHandler import TextractorHandler
from textractor.parsers import response_parser

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger

from botocore.exceptions import ClientError

from status_info_layer.StatusEnum import QuestionStatusEnum

logger = Logger()

PAGE_CHUNK_SIZE = int(os.environ.get("PAGE_CHUNK_SIZE", 20))
dynamo_db_table_name = os.environ.get("JOBS_DYNAMO_DB_TABLE_NAME")
bucket_name = os.environ.get("DOCUMENT_BUCKET_NAME")

textract_client = boto3.client('textract')
table = boto3.resource("dynamodb").Table(dynamo_db_table_name)
s3 = boto3.client('s3')

# TODO: use aws_lambda_powertools.event_handler import APIGatewayRestResolver and CORSConfig to avoid having to
#  know about API GW response formats
def _format_response(handler):
    @functools.wraps(handler)
    def wrapper(event, context):
        response = handler(event, context)
        return {
            "statusCode": response["statusCode"],
            "job_id": response["job_id"],
            "document_key": response["document_key"],
            "document_name":  response["document_name"],
            "pages_chunk_size": response["pages_chunk_size"],
            "total_pages": response["total_pages"],
            "is_in_chunks": response["is_in_chunks"],
            "is_by_page": response["is_by_page"],
            "n_chunks":  response["n_chunks"],
            "chunk_keys": response["chunk_keys"],
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

def textract_get_detection_job(job_id, next_token=None):
    """
    Gets data for a previously started text detection job.

    :param job_id: The ID of the job to retrieve.
    :return: The job data, including a list of blocks that describe elements
             detected in the image.
    """
    try:

        if next_token:
            response = textract_client.get_document_text_detection(JobId=job_id, NextToken=next_token)
        else:
            response = textract_client.get_document_text_detection(JobId=job_id)
        job_status = response["JobStatus"]
        logger.info("Job %s status is %s.", job_id, job_status)
    except ClientError:
        logger.exception("Couldn't get data for job %s.", job_id)
        raise
    else:
        return response

def parse_textract_results(job_id):
    """
    Parse Textract results to a Textractor object
    @param job_id: Textract job id
    @return: Textractor object
    """

    logger.debug(f"Parsing Textract results for job {job_id}")

    detection_job = textract_get_detection_job(job_id)
    textract_results = detection_job.copy()

    while "NextToken" in detection_job:
        logger.debug(f"Getting next token for job {job_id}")
        detection_job = textract_get_detection_job(job_id, detection_job["NextToken"])
        print(detection_job["DocumentMetadata"])
        print(detection_job["JobStatus"])
        print(detection_job.get("NextToken", ""))
        textract_results["Blocks"].extend(detection_job["Blocks"])
        print(detection_job.get("Block appended", ""))

    logger.debug(f"Textract results for job {job_id} parsed")

    logger.debug(f"Parsing Textract results for job {job_id}")
    textractor_document = response_parser.parse(textract_results)
    logger.debug(f"Textract results for job {job_id} parsed")

    return textractor_document


@_format_response
@logger.inject_lambda_context(log_event=True)
def handler(event, _context: LambdaContext):
    """
    Lambda function to chunk a multipage text document
    @param event:
    @param context:
    @return:
    """

    logger.info(f"Received event: {event}")

    queue_message = json.loads(event[-1]["body"])  # Read only the last message

    logger.info(f"\n\nQueue message: {queue_message}")

    textract_result = json.loads(queue_message["Message"])
    logger.info(f"\n\nTextract result: {textract_result}")

    print("\n\nTextract result")
    print(type(textract_result))
    print(textract_result)

    chunk_keys = []

    # Validate Textract Job Status
    if textract_result["Status"] == "SUCCEEDED":
        job_id = textract_result["JobId"]
        document_key = textract_result["JobTag"]

        # Parse textract results to Textractor
        try:
            textractor_document = parse_textract_results(job_id)
        except Exception as e:
            logger.error(f"Error parsing Textract results: {e}")
            table.update_item(
                Key={"job_id": job_id},
                UpdateExpression="SET #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":status": QuestionStatusEnum.ERROR.name},
            )
            raise

        # Chunk document
        try:
            logger.info("Parsing document with textractor")
            textractor_handler = TextractorHandler(logger)
            logger.info("Chunking document")
            response = textractor_handler.get_document_text(textractor_document, chunk_size=PAGE_CHUNK_SIZE, page_overlap=1)
            logger.info("Document chunked")

            # Save chunks to temporary text files
            for i, chunk in enumerate(response["results"]["text"], start=1):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                    temp_file.write(chunk)
                    temp_filename = temp_file.name

                # Upload chunk to S3
                s3.upload_file(temp_filename, bucket_name, f'chunks/{document_key}/chunk_{i}.txt')
                chunk_keys.append(f'chunks/{document_key}/chunk_{i}.txt')
                
                # Clean up temporary file
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)

        except Exception as e:
            logger.error(f"Error chunking document: {e}")
            table.update_item(
                Key={"job_id": job_id},
                UpdateExpression="SET #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":status": QuestionStatusEnum.ERROR.name},
            )
            raise

        #question_analysis = [[(perspective, key) for key in chunk_keys] for perspective in AnalysisPerspectives]

        # Update status in DynamoDB table
        try:
            logger.info(f"Updating DynamoDB job with id:{job_id} and doc key:{document_key}")
            table.update_item(
                Key={"job_id": job_id},
                UpdateExpression="SET #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":status": QuestionStatusEnum.PAGE_CHUNKING.name},
            )
        except Exception as e:
            logger.error(f"Error updating DynamoDB: {e}")
            raise

        # Retrieve job details from DB
        try:
            logger.info(f"Retrieving job details from DynamoDB")
            job_details = table.get_item(Key={"job_id": job_id})["Item"]
        except Exception as e:
            table.update_item(
                Key={"job_id": job_id},
                UpdateExpression="SET #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":status": QuestionStatusEnum.ERROR.name},
            )
            logger.error(f"Error retrieving job details from DynamoDB: {e}")
            raise

        return {
            "statusCode": 200,
            "job_id": job_id,
            "document_key": document_key,
            "document_name": job_details["document_name"],
            'total_pages': response["total_pages"],
            'is_in_chunks': response["is_in_chunks"],
            'is_by_page': response["is_by_page"],
            "pages_chunk_size": PAGE_CHUNK_SIZE,
            "n_chunks": len(response['results']),
            "chunk_keys": chunk_keys
        }
    else:
        return {
            "statusCode": 500,
            "error": "Textract job failed"
        }
