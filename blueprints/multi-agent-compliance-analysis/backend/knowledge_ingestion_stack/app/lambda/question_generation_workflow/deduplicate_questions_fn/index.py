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

import itertools
import logging
import os
import json
import time
import traceback

import boto3
import functools
import langchain_core

from langchain_aws import ChatBedrockConverse

from retrying import retry

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger

from botocore.exceptions import ClientError
from botocore.config import Config

from prompts.generate_questions_prompt import get_unique_questions_prompt_selector

from status_info_layer.StatusEnum import QuestionStatusEnum
from structured_output.questions import DocumentQuestions

class BedrockRetryableError(Exception):
    """Class to identify a Bedrock throttling error"""

    def __init__(self, msg):
        super().__init__(self)

        self.message = msg

langchain_core.globals.set_debug(True)
logger = Logger()

AWS_REGION = os.environ.get("REGION")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID")
LANGUAGE_ID = os.environ.get("LANGUAGE_ID")
JOBS_DYNAMODB_TABLE_NAME = os.environ.get("JOBS_DYNAMO_DB_TABLE_NAME")
COMPLIANCE_DYNAMODB_TABLE_NAME = os.environ.get("COMPLIANCE_DYNAMODB_TABLE_NAME")

QUESTION_BATCH_SIZE = 50

compliance_job_table = boto3.resource("dynamodb").Table(COMPLIANCE_DYNAMODB_TABLE_NAME)
job_table = boto3.resource("dynamodb").Table(JOBS_DYNAMODB_TABLE_NAME)

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
@retry(wait_exponential_multiplier=10000, wait_exponential_max=60000, stop_max_attempt_number=10,
       retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
def deduplicate_questions(
        country: str,
        industry: str,
        workload: str,
        questions: list[str],
):

    print("All questions")
    print(questions)

    questions_llm = ChatBedrockConverse(
        model=MODEL_ID,
        temperature=0.1,
        max_tokens=10000,
        top_p=0.9
        # other params...
    )

    ############----------Chain action---------############
    LLM_DEDUPLICATE_QUESTIONS_PROMPT_SELECTOR = get_unique_questions_prompt_selector(lang="en")
    question_deduplication_prompt = LLM_DEDUPLICATE_QUESTIONS_PROMPT_SELECTOR.get_prompt(MODEL_ID)
    question_deduplication_chain = question_deduplication_prompt | questions_llm.with_structured_output(DocumentQuestions)

    try:

        # Deduplicate by batches of 50 questions


        unique_questions = question_deduplication_chain.invoke(
            {
                "industry": industry,
                "country": country,
                "workload": workload,
                "questions": questions
            }
        )

        return unique_questions.questions
    except ClientError as exc:
        if exc.response['Error']['Code'] == 'ThrottlingException':
            logger.error("Bedrock throttling. To try again")
            raise BedrockRetryableError(str(exc))
        elif exc.response['Error']['Code'] == 'ModelTimeoutException':
            logger.error("Bedrock ModelTimeoutException. To try again")
            raise BedrockRetryableError(str(exc))
        elif exc.response['Error']['Code'] == 'ModelErrorException':
            logger.error("Bedrock ModelErrorException. To try again")
            raise BedrockRetryableError(str(exc))
        else:
            raise
    except bedrock_runtime.exceptions.ThrottlingException as throttlingExc:
        logger.error("Bedrock ThrottlingException. To try again")
        raise BedrockRetryableError(str(throttlingExc))
    except bedrock_runtime.exceptions.ModelTimeoutException as timeoutExc:
        logger.error("Bedrock ModelTimeoutException. To try again")
        raise BedrockRetryableError(str(timeoutExc))
    except bedrock_runtime.exceptions.ModelErrorException as modelErrExc:
        logger.error("Bedrock ModelErrorException. To try again")
        raise BedrockRetryableError(str(modelErrExc))
    except Exception as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        logger.error(message)
        raise

@_format_response
@logger.inject_lambda_context(log_event=True)
def handler(event, _context: LambdaContext):
    """
    Lambda function to create multiple perspectives per chunk
    @param event:
    @param context:
    @return:
    """

    question_aggregate = []
    unique_questions = []

    logger.info(f"Received event: {event}")

    #Retrieve main job id
    document_job_id = event["job_id"]
    document_key = event["document_key"]
    document_name = event["document_name"]

    try:

        logger.info(f"Document ID: {document_job_id}")
        main_job_id = get_main_job_from_document_job(document_job_id)

        #Retrieve compliance job details
        main_job_details = get_main_job_details(main_job_id)
        workload = main_job_details["workload"]
        country = main_job_details["country"]
        industry = main_job_details["industry"]

        logger.debug(f"De-duplicating questions for {workload} process")
        logger.debug(event['questions'])

        for questions in event['questions']:
            question_aggregate.extend(questions)

    except Exception as e:
        job_table.update_item(
            Key={"job_id": event["job_id"]},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": QuestionStatusEnum.ERROR.name},
        )
        logger.error(f"Error getting questions set: {e}")
        traceback.print_exc()
        raise (e)

    try:

        # First deduplicate by batch of questions to avoid
        for question_batch in itertools.batched(question_aggregate, QUESTION_BATCH_SIZE):
            unique_batch_questions = deduplicate_questions(
                country,
                industry,
                workload,
                list(question_batch)
            )
            unique_questions.extend(unique_batch_questions)

    except Exception as e:
        job_table.update_item(
            Key={"job_id": event["job_id"]},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": QuestionStatusEnum.ERROR.name},
        )
        logger.error(f"Error deduplicating questions: {e}")
        traceback.print_exc()
        raise (e)

    try:

        # Run a final deduplication with all the questions in the set
        unique_questions = deduplicate_questions(
            country,
            industry,
            workload,
            unique_questions
        )

        print("Unique questions")
        print(unique_questions)

    except Exception as e:
        job_table.update_item(
            Key={"job_id": event["job_id"]},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": QuestionStatusEnum.ERROR.name},
        )
        logger.error(f"Error deduplicating all questions but will continue with current batch: {e}")
        pass

    # Update job status in DynamoDB table
    try:

        job_table.update_item(
            Key={"job_id": document_job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": QuestionStatusEnum.DOCUMENT_QUESTION_CONSOLIDATION.name},
        )

    except Exception as e:

        logger.error(f"Error updating DynamoDB: {e}")
        traceback.print_exc()
        raise (e)

    return {
        "statusCode": 200,
        "document_key": document_key,
        "document_name": document_name,
        "job_id": document_job_id,
        "body": {
            "questions": unique_questions
        }
    }
