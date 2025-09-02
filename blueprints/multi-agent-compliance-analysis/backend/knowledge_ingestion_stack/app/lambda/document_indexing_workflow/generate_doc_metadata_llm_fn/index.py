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

STRUCTURED_OUTPUT_MODEL_TEMP = 0.2

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=BEDROCK_REGION,
    config=Config(
        connect_timeout=180,
        read_timeout=180,
        retries={
            "max_attempts": 50,
            "mode": "adaptive",
        },
    )
)

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
def generate_doc_metadata(
        metadata_chunks:str
):
    global STRUCTURED_OUTPUT_MODEL_TEMP

    metadata_llm = ChatBedrockConverse(
        model=MODEL_ID,
        temperature=STRUCTURED_OUTPUT_MODEL_TEMP if STRUCTURED_OUTPUT_MODEL_TEMP < 1 else 1,
        max_tokens=1500,
        # other params...
    )

     # Derive metadata from all chunks

    LLM_GENERATE_METADATA_PROMPT_SELECTOR = get_metadata_prompt_selector(lang="en")
    gen_medatata_prompt = LLM_GENERATE_METADATA_PROMPT_SELECTOR.get_prompt(MODEL_ID)
    structured_metadata = metadata_llm.with_structured_output(DocumentMetadata)

    structured_metadata_prompt = gen_medatata_prompt | structured_metadata

    document_metadata = structured_metadata_prompt.invoke(
        {
            "metadata_by_chunks": metadata_chunks,
        }
    )

    try:
        response = document_metadata

        return response
    except ClientError as exc:
        if exc.response['Error']['Code'] == 'ThrottlingException':
            logger.error("Bedrock throttling. To try again")
            raise BedrockRetryableError(str(exc))
        elif exc.response['Error']['Code'] == 'ModelTimeoutException':
            logger.error("Bedrock ModelTimeoutException. To try again")
            raise BedrockRetryableError(str(exc))
        elif exc.response['Error']['Code'] == 'ModelErrorException':
            STRUCTURED_OUTPUT_MODEL_TEMP = STRUCTURED_OUTPUT_MODEL_TEMP + 0.1
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
        STRUCTURED_OUTPUT_MODEL_TEMP = STRUCTURED_OUTPUT_MODEL_TEMP + 0.1
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

    document_key = event[0]["document_key"]
    document_name = event[0]["document_name"]

    metadata_list = [None] * len(event)

    metadata_chunks = ""

    # loop through the results
    for element in event:
        logger.debug(element)

        # Validate no chunks from other Job Id are present
        if document_key != element["document_key"]:
            # Update status in DynamoDB table
            try:
                jobsTable.update_item(
                    Key={"document_key": document_key},
                    UpdateExpression="SET #status = :status",
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={":status": IndexingStatusEnum.ERROR.name},
                )
            except Exception as e:
                logger.error(f"Error updating DynamoDB: {e}")
                raise

            raise ValueError("All elements must have the same job_id")

        logger.info(f"Processing elements for chunk: {element['chunk_index']}")

        metadata_list[element['chunk_index']] = element['MetadataTask']['metadata']
        metadata_chunks = "\n\n".join(
            f"<metadata_chunk_{i}> \n{text}\n </metadata_chunk_{i}>" for i, text in enumerate(metadata_list, start=1)
        )

    try:

        llm_metadata_completion = generate_doc_metadata(
            metadata_chunks
        )

        metadata = llm_metadata_completion.model_dump()

        logger.debug(f"Generated metadata: {metadata}")

    except Exception as e:
        logger.error(f"Error generating metadata: {e}")
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
            UpdateExpression="SET #json_metadata = :json_metadata",
            ExpressionAttributeNames={"#json_metadata": "json_metadata"},
            ExpressionAttributeValues={":json_metadata": json.dumps(metadata)},
        )

        jobsTable.update_item(
            Key={"document_key": document_key},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": IndexingStatusEnum.METADATA_CONSOLIDATION.name},
        )

    except Exception as e:

        logger.error(f"Error updating DynamoDB: {e}")
        traceback.print_exc()
        raise(e)

    return {
        "statusCode": 200,
        "body": {
            "document_key": document_key,
            "doc_metadata": metadata,
            "document_name": document_name
        }
    }