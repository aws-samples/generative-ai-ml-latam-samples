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
import traceback
import tempfile

import boto3
import os
import functools
import langchain_core

from retrying import retry

from aws_lambda_powertools import Logger

from langchain_aws import ChatBedrockConverse

from botocore.exceptions import ClientError
from botocore.config import Config

from prompt_selector.generate_metadata_prompt import get_metadata_prompt_selector
from structured_output.metadata import DocumentMetadata

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
#DOCUMENTS_DYNAMODB_TABLE_NAME = os.environ.get("DOCUMENTS_DYNAMO_DB_TABLE_NAME")
JOBS_DYNAMODB_TABLE_NAME = os.environ.get("JOBS_DYNAMO_DB_TABLE_NAME")
DOCUMENTS_BUCKET_NAME = os.environ.get("DOCUMENT_BUCKET_NAME")

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=BEDROCK_REGION,
    config=Config(retries={'max_attempts': 20})
)
s3 = boto3.client('s3')

#documentsTable = boto3.resource("dynamodb").Table(DOCUMENTS_DYNAMODB_TABLE_NAME)
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

# A function to extract metadata from the document
@retry(wait_exponential_multiplier=10000, wait_exponential_max=900000, stop_max_attempt_number=8,
       retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
def extract_metadata(
        document_name:str,
        text:str
):
    metadata_llm = ChatBedrockConverse(
        model=MODEL_ID,
        temperature=0.1,
        max_tokens=700,
        top_p=0.9
        # other params...
    )

    LLM_GENERATE_METADATA_PROMPT_SELECTOR = get_metadata_prompt_selector(lang="en")

    gen_medatata_prompt = LLM_GENERATE_METADATA_PROMPT_SELECTOR.get_prompt(MODEL_ID)

    messages = gen_medatata_prompt.format_messages(
        document_types=", ".join([doc_type.value for doc_type in DocumentTypes]),
        doc_title=document_name,
        text=text,
        metadata_object_definition=DocumentMetadata.model_json_schema()
    )

    # Create messages
    msgs = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": messages[0].content,
                },
                {
                    "cachePoint": {"type": "default"}   # Need to create messages for prompt caching
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": messages[1].content
                }
            ]
        }
    ]

    try:
        response = metadata_llm.invoke(msgs)

        return response
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


def handler(event, context):
    """
    Lambda function to extract metadata from document
    Lambda function to chunk a multipage text document
    @param event:
    @param context:
    @return:
    """

    #logger.info(f"Received event: {event}")
    logger.info(f"Received variable for DB: {JOBS_DYNAMODB_TABLE_NAME}")

    chunk_s3_key = event["chunk_s3_key"]
    chunk_index = event["chunk_index"]
    document_key = event["document_key"]
    document_name = event["document_name"]

    try:

        # Download file from S3 using secure temporary file
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        try:
            s3.download_file(DOCUMENTS_BUCKET_NAME, chunk_s3_key, temp_filename)
            
            with open(temp_filename, "r") as f:
                text_chunk = f.read()
        finally:
            # Clean up temporary file
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    except Exception as e:
        logger.error(f"Error downloading chunk: {e}")
        jobsTable.update_item(
            Key={"document_key": document_key},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": IndexingStatusEnum.ERROR.name},
        )
        raise

    try:

        llm_metadata_completion = extract_metadata(
            document_name,
            text_chunk
        )

        metadata = llm_metadata_completion.content

        logger.info(f"Extracted metadata: {metadata}")

    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
        traceback.print_exc()
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
            ExpressionAttributeValues={":status": IndexingStatusEnum.METADATA_EXTRACTION.name},
        )

    except Exception as e:

        logger.error(f"Error updating DynamoDB: {e}")
        traceback.print_exc()
        raise

    return {
        "statusCode": 200,
        "body": {
            "document_key": document_key,
            "doc_metadata": metadata,
            "document_name": document_name,
            "chunk_index": chunk_index
        }
    }