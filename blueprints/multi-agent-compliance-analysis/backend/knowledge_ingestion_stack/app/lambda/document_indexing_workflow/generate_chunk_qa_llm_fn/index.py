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
import pydantic
import langchain_core

from retrying import retry

from aws_lambda_powertools import Logger

from langchain_aws import ChatBedrockConverse

from botocore.exceptions import ClientError
from botocore.config import Config

from prompt_selector.generate_qa_prompt import get_qa_prompt_selector, get_structured_qa_prompt_selector
from structured_output.question_answers import QA_pairs

from status_info_layer.StatusEnum import IndexingStatusEnum
from analysis_lenses.user_analysis_mapping import AnalysisPersonas

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
MAX_N_QUESTIONS = int(os.environ.get("MAX_N_QUESTIONS", 20))
STRUCTURED_MODEL_ID = os.environ.get("STRUCTURED_MODEL_ID")
JOBS_DYNAMODB_TABLE_NAME = os.environ.get("JOBS_DYNAMO_DB_TABLE_NAME")
DOCUMENTS_BUCKET_NAME = os.environ.get("DOCUMENT_BUCKET_NAME")

STRUCTURED_OUTPUT_MODEL_TEMP = 0.1
MAX_INPUT_TOKEN_COUNT = 5000

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
            "document_key": response["document_key"],
            "document_name": response["document_name"],
            "chunk_index": response["chunk_index"],
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


# A function to generate questions as Pydantic object
@retry(wait_exponential_multiplier=10000, wait_exponential_max=500000, stop_max_attempt_number=4,
       retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
def generate_structured_qa_set(
        qa_text: str,
):
    global STRUCTURED_OUTPUT_MODEL_TEMP

    questions_llm = ChatBedrockConverse(
        model=STRUCTURED_MODEL_ID,
        temperature=STRUCTURED_OUTPUT_MODEL_TEMP,
        max_tokens=int(MAX_INPUT_TOKEN_COUNT*1.15),
        # other params...
    )

    LLM_GENERATE_STRUCTURED_QUESTIONS_PROMPT_SELECTOR = get_structured_qa_prompt_selector(lang="en")
    gen_structured_questions_prompt = LLM_GENERATE_STRUCTURED_QUESTIONS_PROMPT_SELECTOR.get_prompt(MODEL_ID)
    structured_questions = questions_llm.with_structured_output(QA_pairs)

    structured_questions_llm = gen_structured_questions_prompt | structured_questions

    try:
        response = structured_questions_llm.invoke(
            {
                "qa_text": qa_text,
            }
        )

        logger.info("The extracted Q&A set is:")
        logger.info(response)

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

# A function to generate questions from the document
@retry(wait_exponential_multiplier=10000, wait_exponential_max=900000, stop_max_attempt_number=8,
       retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
def generate_questions(
        document_name:str,
        analysis_perspective:str,
        user_type:str,
        text:str
):

    global STRUCTURED_OUTPUT_MODEL_TEMP

    print("\n\nModel temp\n\n")
    print(STRUCTURED_OUTPUT_MODEL_TEMP)

    qa_llm = ChatBedrockConverse(
        model=MODEL_ID,
        temperature=STRUCTURED_OUTPUT_MODEL_TEMP if STRUCTURED_OUTPUT_MODEL_TEMP < 1 else 1,
        max_tokens=7000,
        top_p=0.9
        # other params...
    )

    logger.info(f"Generating questions for {document_name} with {analysis_perspective} perspective")

    LLM_GENERATE_QA_PROMPT_SELECTOR = get_qa_prompt_selector(lang="en")
    gen_qa_prompt = LLM_GENERATE_QA_PROMPT_SELECTOR.get_prompt(MODEL_ID)

    messages = gen_qa_prompt.format_messages(
        user_type= user_type,
        doc_title= document_name,
        topic_perspective= analysis_perspective,
        n_pairs= MAX_N_QUESTIONS,
        text= text
    )

    # Create messages
    msgs = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": messages[0].content,
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": messages[1].content
                },
                {
                    "cachePoint": {"type": "default"}  # Need to create messages for prompt caching
                }
            ]
        }
    ]

    try:
        qa_set = qa_llm.with_structured_output(QA_pairs).invoke(msgs)

        return qa_set

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
    except pydantic.ValidationError as dataTypeValError:
        STRUCTURED_OUTPUT_MODEL_TEMP = STRUCTURED_OUTPUT_MODEL_TEMP + 0.1
        logger.error("Pydantic Validation Error. To try again")
        raise BedrockRetryableError(str(dataTypeValError))
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

    logger.info(f"Received event: {event}")

    chunk_s3_key = event["chunk_s3_key"]
    chunk_index = event["chunk_index"]
    document_key = event["document_key"]
    document_name = event["document_name"]

    qa_pairs = {}

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

        # Generate pairs of questions and answers for each pair of persona-analysis type

        users = AnalysisPersonas.keys()

        for user in users:
            qa_pairs[user] = {}
            logger.info(f"Generating QA for user: {user}")
            logger.debug(f"User perspectives: {AnalysisPersonas[user]['perspectives']}")
            for perspective in AnalysisPersonas[user]["perspectives"]:
                logger.debug(f"Generating QA for user: {user} and perspective: {perspective}")
                qa_set = generate_questions(
                    document_name,
                    perspective,
                    user,
                    text_chunk
                )

                #qa_completion = llm_qa_completion.content
                #QAset = generate_structured_qa_set(qa_completion)
                qa_pairs[user][perspective] = qa_set.model_dump()
                print("\n\n QA set \n\n")
                print(qa_set)
                #qa_pairs[user][perspective].model_dump()

        logger.debug(f"Generated QA: {qa_pairs}")

    except Exception as e:
        logger.error(f"Error generating QA: {e}")
        traceback.print_exc()
        jobsTable.update_item(
            Key={"document_key": document_key},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": IndexingStatusEnum.ERROR.name},
        )
        raise(e)

    # Save QA pairs to S3
    try:
        # Create secure temporary file for QA data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_qa_file:
            json.dump(qa_pairs, temp_qa_file)
            temp_qa_filename = temp_qa_file.name
        
        try:
            s3.upload_file(temp_qa_filename, DOCUMENTS_BUCKET_NAME, f'chunks/{document_key}/qa_chunk_{chunk_index}.json')
        finally:
            # Clean up temporary file
            if os.path.exists(temp_qa_filename):
                os.unlink(temp_qa_filename)
    except Exception as e:
        logger.error(f"Error saving QA pairs to S3: {e}")
        traceback.print_exc()
        jobsTable.update_item(
            Key={"document_key": document_key},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": IndexingStatusEnum.ERROR.name},
        )
        raise(e)

    # Update job status in DynamoDB table
    try:

        jobsTable.update_item(
            Key={"document_key": document_key},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": IndexingStatusEnum.QA_GENERATION.name},
        )

    except Exception as e:

        logger.error(f"Error updating DynamoDB: {e}")
        traceback.print_exc()
        raise(e)

    return {
        "statusCode": 200,
        "document_key": document_key,
        "document_name": document_name,
        "chunk_index": chunk_index
    }