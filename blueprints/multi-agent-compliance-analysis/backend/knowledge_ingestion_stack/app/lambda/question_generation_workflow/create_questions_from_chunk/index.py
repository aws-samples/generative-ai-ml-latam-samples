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
import tempfile

import boto3
import functools
import langchain_core

from retrying import retry

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger

from botocore.exceptions import ClientError
from botocore.config import Config

from status_info_layer.StatusEnum import QuestionStatusEnum
from QuestionGeneratorAgent import QuestionGenerationSelfReflexionAgent

class BedrockRetryableError(Exception):
    """Class to identify a Bedrock throttling error"""

    def __init__(self, msg):
        super().__init__(self)

        self.message = msg

langchain_core.globals.set_debug(True)
logger = Logger()

AWS_REGION = os.environ.get("REGION")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION")
ACTOR_MODEL_ID = os.environ.get("BEDROCK_ACTOR_MODEL_ID")
EVALUATOR_MODEL_ID = os.environ.get("BEDROCK_EVALUATOR_MODEL_ID")
FEEDBACK_MODEL_ID = os.environ.get("BEDROCK_FEEDBACK_MODEL_ID")
STRUCTURED_OUTPUT_MODEL_ID = os.environ.get("BEDROCK_STRUCTURED_OUTPUT_MODEL_ID")
LANGUAGE_ID = os.environ.get("LANGUAGE_ID")
MAX_N_QUESTIONS = os.environ.get("MAX_N_QUESTIONS", "20")
REFLEXION_MIN_SCORE = float(os.environ.get("REFLEXION_MIN_SCORE", 0.85))
MAX_TRIALS = int(os.environ.get("MAX_TRIALS", 3))
JOBS_DYNAMODB_TABLE_NAME = os.environ.get("JOBS_DYNAMO_DB_TABLE_NAME")
COMPLIANCE_DYNAMODB_TABLE_NAME = os.environ.get("COMPLIANCE_DYNAMODB_TABLE_NAME")
DOCUMENTS_BUCKET_NAME = os.environ.get("DOCUMENTS_BUCKET_NAME")

job_table = boto3.resource("dynamodb").Table(JOBS_DYNAMODB_TABLE_NAME)
compliance_job_table = boto3.resource("dynamodb").Table(COMPLIANCE_DYNAMODB_TABLE_NAME)
s3 = boto3.client('s3')

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=BEDROCK_REGION,
    config=Config(retries={'max_attempts': 20})
)

# TODO: use aws_lambda_powertools.event_handler import APIGatewayRestResolver and CORSConfig to avoid having to
#  know about API GW response formats
def _format_response(handler):
    @functools.wraps(handler)
    def wrapper(event, context):
        response = handler(event, context)
        return {
            "statusCode": response["statusCode"],
            "document_key":  response["document_key"],
            "document_name": response["document_name"],
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

def get_main_job_from_document_job(
        document_job_id
):
    """
    Get the main job associated with this job
    @param user:
    @param perspective:
    @return:
    """
    try:
        response = job_table.get_item(
            Key={
                "job_id": document_job_id,
            }
        )
        if "Item" in response:
            item = response["Item"]
            return item["main_job_id"]
        else:
            return ""
    except ClientError as ex:
        logger.error(f"Job {document_job_id} does not exist")
        raise ex

def get_main_job_details(
        main_job_id
):
    """
    Get the main job associated with this job
    @param user:
    @param perspective:
    @return:
    """
    try:
        response = compliance_job_table.get_item(
            Key={
                "job_id": main_job_id,
            }
        )
        if "Item" in response:
            return response["Item"]
        else:
            return ""
    except ClientError as ex:
        logger.error(f"Job {main_job_id} does not exist")
        raise ex

# A function to generate questions from the document
def generate_questions(
        country: str,
        industry: str,
        workload: str,
        text_chunk: str,
        reference_questions: list[str],
):

    print("Gold standard questions")
    print(reference_questions)

    self_reflection_agent = QuestionGenerationSelfReflexionAgent(
        industry=industry,
        country=country,
        workload=workload,
        action_model_id=ACTOR_MODEL_ID,
        evaluator_model_id=EVALUATOR_MODEL_ID,
        reflexion_model_id=FEEDBACK_MODEL_ID,
        structured_output_model_id=STRUCTURED_OUTPUT_MODEL_ID,
        gold_standard_questions=reference_questions,
        expected_score=REFLEXION_MIN_SCORE,
        max_trials=MAX_TRIALS,
        logger=logger,
        bedrock_region=BEDROCK_REGION
    )

    self_reflection_agent.execute_task(
        n_questions=MAX_N_QUESTIONS,
        regulation_portion=text_chunk
    )

    return self_reflection_agent.current_qa

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

    question_by_perspective = {}

    document_job_id = event["job_id"]
    logger.info(f"Document ID: {document_job_id}")

    try:

        #Retrieve main job id
        main_job_id = get_main_job_from_document_job(document_job_id)

    except Exception as e:
        logger.error(f"Error retrieving analysis id: {e}")
        job_table.update_item(
            Key={"job_id": event["job_id"]},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": QuestionStatusEnum.ERROR.name},
        )
        raise

    try:
        #Retrieve compliance job details
        main_job_details = get_main_job_details(main_job_id)
        workload = main_job_details["workload"]
        country = main_job_details["country"]
        industry = main_job_details["industry"]
        reference_questions = json.loads(main_job_details["gold_standard_questions"])
    except Exception as e:
        logger.error(f"Error retrieving analysis details: {e}")
        job_table.update_item(
            Key={"job_id": event["job_id"]},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": QuestionStatusEnum.ERROR.name},
        )
        raise

    try:

        # Download file from S3 using temporary file
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        s3.download_file(DOCUMENTS_BUCKET_NAME, event["chunk_s3_key"], temp_filename)

        with open(temp_filename, "r") as f:
            text_chunk = f.read()
        
        # Clean up temporary file
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)

        logger.debug(f"Downloaded text chunk")
        logger.debug(text_chunk)

        logger.debug("Questions")
        logger.debug(reference_questions)

        logger.debug(f"Generating questions for {workload} process")
        questions = generate_questions(
            country,
            industry,
            workload,
            text_chunk,
            reference_questions,
        )
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        job_table.update_item(
            Key={"job_id": event["job_id"]},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": QuestionStatusEnum.ERROR.name},
        )
        raise

    # Update job status in DynamoDB table
    try:

        job_table.update_item(
            Key={"job_id": document_job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": QuestionStatusEnum.CHUNK_QUESTION_GENERATION.name},
        )

    except Exception as e:

        logger.error(f"Error updating DynamoDB: {e}")
        traceback.print_exc()
        raise (e)


    return {
        "statusCode": 200,
        "document_key": event["document_key"],
        "document_name": event["document_name"],
        "job_id": event["job_id"],
        "body": {
            "questions": questions
        }
    }
