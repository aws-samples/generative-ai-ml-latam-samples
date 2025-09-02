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

import boto3
import os
import json
import functools
import itertools
import traceback
import tempfile
import langchain_core

from retrying import retry

from aws_lambda_powertools import Logger

from langchain_aws import ChatBedrockConverse

from botocore.exceptions import ClientError
from botocore.config import Config

from prompt_selector.generate_meta_kb_prompt import get_summary_prompt_selector

from status_info_layer.StatusEnum import IndexingStatusEnum
from analysis_lenses.document_types import DocumentTypes

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
DOCUMENTS_DYNAMODB_TABLE_NAME = os.environ.get("DOCUMENTS_DYNAMO_DB_TABLE_NAME")
JOBS_DYNAMODB_TABLE_NAME = os.environ.get("JOBS_DYNAMO_DB_TABLE_NAME")
DOCUMENTS_BUCKET_NAME = os.environ.get("DOCUMENT_BUCKET_NAME")

MAX_QA_PER_BATCH = 50

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=BEDROCK_REGION,
    config=Config(retries={'max_attempts': 20})
)
s3 = boto3.client('s3')

documentsTable = boto3.resource("dynamodb").Table(DOCUMENTS_DYNAMODB_TABLE_NAME)
jobsTable = boto3.resource("dynamodb").Table(JOBS_DYNAMODB_TABLE_NAME)

# TODO: use aws_lambda_powertools.event_handler import APIGatewayRestResolver and CORSConfig to avoid having to
#  know about API GW response formats
def _format_response(handler):
    @functools.wraps(handler)
    def wrapper(event, context):
        response = handler(event, context)
        return {
            "statusCode": response["statusCode"],
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


def get_existing_summary(
        user,
        perspective
):
    """
    Get an existing summary, if exists, for a combination of user and perspective.
    @param user:
    @param perspective:
    @return:
    """
    try:
        response = documentsTable.get_item(
            Key={
                "summary_key": f"{user}-{perspective}",
            }
        )
        if "Item" in response:
            item = response["Item"]
            return item["summary"]
        else:
            return ""
    except ClientError as ex:
        logger.error(f"Summary for {user}-{perspective} does not exist")
        raise ex

# A function to generate a meta-knowledge summary
@retry(wait_exponential_multiplier=10000, wait_exponential_max=500000, stop_max_attempt_number=4,
       retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
def generate_mk_summary(
        analysis_perspective:str,
        user_type:str,
        qa_str:str,
        previous_summary:str=""
):
    mk_summary_llm = ChatBedrockConverse(
        model=MODEL_ID,
        temperature=0.4,
        max_tokens=5000,
        top_p=0.9
        # other params...
    )

    LLM_GENERATE_SUMMARY_PROMPT_SELECTOR = get_summary_prompt_selector(lang="en", with_context=True if previous_summary else False, for_chunks=False)
    gen_summary_prompt = LLM_GENERATE_SUMMARY_PROMPT_SELECTOR.get_prompt(MODEL_ID)
    summary_prompt = gen_summary_prompt | mk_summary_llm

    try:

        logger.info("Attempting to generate summary")
        mk_summary = summary_prompt.invoke(
            {
                "document_types": ", ".join([doc_type.value for doc_type in DocumentTypes]),
                "topic_perspective": analysis_perspective,
                "users_types": user_type,
                "qa_pairs": qa_str,
                "summary": previous_summary
            }
        )
        logger.debug("Summary generated")
        logger.debug(mk_summary.content)

        return mk_summary.content

    except ClientError as exc:
        logger.error("Bedrock Exception")

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
        logger.error("Bedrock Exception")
        logger.error("Bedrock ThrottlingException. To try again")
        raise BedrockRetryableError(str(throttlingExc))
    except bedrock_runtime.exceptions.ModelTimeoutException as timeoutExc:
        logger.error("Bedrock Exception")
        logger.error("Bedrock ModelTimeoutException. To try again")
        raise BedrockRetryableError(str(timeoutExc))
    except bedrock_runtime.exceptions.ModelErrorException as modelErrExc:
        logger.error("Bedrock Exception")
        logger.error("Bedrock ModelErrorException. To try again")
        raise BedrockRetryableError(str(modelErrExc))
    except Exception as e:
        logger.error("Bedrock Exception")
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        logger.error(message)
        raise

def handler(event, context):
    """
    Lambda function to generate a meta-summary for a KB
    @param event:
    @param context:
    @return:
    """

    logger.info(f"Received event: {event}")

    doc_name = event["document_name"]
    document_key = event["document_key"]
    metadata = event["metadata"]

    summaries =  {}

    try:

        # Download file from S3
        print(f"Downloading file from S3: {DOCUMENTS_BUCKET_NAME}/{document_key}")
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
            localFilename = temp_file.name
        
        s3.download_file(DOCUMENTS_BUCKET_NAME, os.path.join("qa", document_key, "qa_doc.json"), localFilename)

        with open(localFilename, 'r') as f:
            qa_pairs = json.load(f)

        # Clean up temporary file
        if os.path.exists(localFilename):
            os.unlink(localFilename)
        
        logger.debug(f"QA pairs: {qa_pairs}")
    except Exception as e:
        logger.error(f"Error downloading QA document: {e}")
        jobsTable.update_item(
            Key={"document_key": document_key},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": IndexingStatusEnum.ERROR.name},
        )
        raise

    try:

        # Generate meta-knowledge summary for each combination of user-perspective
        for user in qa_pairs:
            print(f"For user: {user}")
            summaries[user] = {}
            for perspective in qa_pairs[user]:

                logger.debug(f"Generating summary for {user}-{perspective}")
                logger.debug(qa_pairs[user][perspective])

                user_perspective_qa = qa_pairs[user][perspective]
                logger.debug("User-Perspective QA")
                logger.debug(user_perspective_qa)

                summary = get_existing_summary(user, perspective)
                logger.debug("User-Perspective Summary")
                logger.debug(summary)

                batch_number = 0
                for user_perspective_qa_batch in itertools.batched(user_perspective_qa, MAX_QA_PER_BATCH):

                    logger.debug(f"Processing batch {batch_number}")
                    logger.debug(user_perspective_qa_batch)

                    document_qa_str = ""

                    for i, batch_qa_pair in enumerate(user_perspective_qa_batch):
                        document_qa_str += f"{i+1}.- {batch_qa_pair['question']}\n{batch_qa_pair['answer']}\n\n"

                    logger.debug("Batch QA")
                    logger.debug(document_qa_str)

                    new_summary = generate_mk_summary(
                        analysis_perspective=perspective,
                        user_type=user,
                        qa_str=document_qa_str,
                        previous_summary=summary
                    )
                    summary = summary + new_summary
                    logger.debug(f"Summary for: {user}-{perspective}")
                    logger.debug(summary)

                    batch_number = batch_number+1

                summaries[user][perspective] = summary

        logger.info(f"Generated summaries: {summaries}")

    except Exception as e:
        logger.error(f"Error generating meta-summary: {e}")
        jobsTable.update_item(
            Key={"document_key": document_key},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": IndexingStatusEnum.ERROR.name},
        )
        traceback.print_exc()
        raise(e)

    # Create a summary for each user-perspective
    try:
        for user in summaries.keys():
            for perspective in summaries[user].keys():
                documentsTable.put_item(
                    Item={
                        "summary_key": f"{user}-{perspective}",
                        "summary": summaries[user][perspective],
                    }
                )
    except Exception as e:
        logger.error(f"Error writing summary to DynamoDB: {e}")
        jobsTable.update_item(
            Key={"document_key": document_key},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": IndexingStatusEnum.ERROR.name},
        )
        raise

    # Update job status in DynamoDB table
    try:

        jobsTable.update_item(
            Key={"document_key": document_key},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": IndexingStatusEnum.SUMMARY_GENERATION.name},
        )

    except Exception as e:
        logger.error(f"Error updating DynamoDB: {e}")
        traceback.print_exc()
        raise(e)

    return {
        "statusCode": 200,
        "body": {
            "document_key": document_key,
            "document_name": doc_name,
            "metadata": metadata,
        }
    }