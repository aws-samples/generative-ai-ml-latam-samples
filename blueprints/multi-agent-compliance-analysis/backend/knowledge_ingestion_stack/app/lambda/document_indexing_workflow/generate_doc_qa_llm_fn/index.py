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
import pydantic
import langchain_core
import tempfile

from retrying import retry

from aws_lambda_powertools import Logger

from langchain_aws import ChatBedrockConverse

from botocore.exceptions import ClientError
from botocore.config import Config

from prompt_selector.generate_qa_prompt import get_qa_prompt_selector, get_structured_qa_prompt_selector
from structured_output.question_answers import QA_pairs

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
STRUCTURED_MODEL_ID = os.environ.get("STRUCTURED_MODEL_ID")
LANGUAGE_ID = os.environ.get("LANGUAGE_ID")
JOBS_DYNAMODB_TABLE_NAME = os.environ.get("JOBS_DYNAMO_DB_TABLE_NAME")
DOCUMENTS_BUCKET_NAME = os.environ.get("DOCUMENT_BUCKET_NAME")

STRUCTURED_OUTPUT_MODEL_TEMP = 0.1
MAX_INPUT_TOKEN_COUNT = 4000

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
            "documentKey": response["documentKey"],
            "documentName": response["documentName"],
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

def read_qa_from_s3(
        document_key,
        n_chunks
):

    qa_pairs = []

    # Download file from S3
    print(f"Downloading files from S3: {DOCUMENTS_BUCKET_NAME}/{document_key}")
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
        localFilename = temp_file.name

    for i in range(n_chunks):
        chunk_s3_key = f'chunks/{document_key}/qa_chunk_{i}.json'
        s3.download_file(DOCUMENTS_BUCKET_NAME, chunk_s3_key, localFilename)

        with open(localFilename) as f:
            qa_pairs.append(json.load(f))
            print(qa_pairs)
            f.close()
    
    # Clean up temp file
    if os.path.exists(localFilename):
        os.unlink(localFilename)

    return qa_pairs


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

        logger.debug("The extracted Q&A set is:")
        logger.debug(response)

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
@retry(wait_exponential_multiplier=10000, wait_exponential_max=500000, stop_max_attempt_number=4,
       retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
def generate_unique_questions_from_chunks(
        persona: str,
        perspective: str,
        qa_chunks_str:str
):
    questions_llm = ChatBedrockConverse(
        model=MODEL_ID,
        temperature=0.1,
        max_tokens=int(MAX_INPUT_TOKEN_COUNT*1.15),
        top_p=0.9
        # other params...
    )

    LLM_GENERATE_QUESTIONS_PROMPT_SELECTOR = get_qa_prompt_selector(lang="en")
    gen_questions_prompt = LLM_GENERATE_QUESTIONS_PROMPT_SELECTOR.get_prompt(MODEL_ID)
    generate_unique_questions_llm = gen_questions_prompt | questions_llm

    try:
        response = generate_unique_questions_llm.invoke(
            {
                "role": persona,
                "perspective": perspective,
                "qa_by_chunks": qa_chunks_str
            }
        )

        return response.content
    except ClientError as exc:
        if exc.response['Error']['Code'] == 'ThrottlingException':
            logger.error("Bedrock throttling. To try again")
            raise BedrockRetryableError(str(exc))
        elif exc.response['Error']['Code'] == 'ModelTimeoutException':
            logger.error("Bedrock ModelTimeoutException. To try again")
            raise BedrockRetryableError(str(exc))
        else:
            raise
    except bedrock_runtime.exceptions.ThrottlingException as throttlingExc:
        logger.error("Bedrock ThrottlingException. To try again")
        raise BedrockRetryableError(str(throttlingExc))
    except bedrock_runtime.exceptions.ModelTimeoutException as timeoutExc:
        logger.error("Bedrock ModelTimeoutException. To try again")
        raise BedrockRetryableError(str(timeoutExc))
    except Exception as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        logger.error(message)
        raise

def generate_unique_questions_by_persona_perspective(
        persona: str,
        perspective: str,
        qa_sets: dict[any]
):
    """Given a set of qa by persona and perspective generate (using LLMs) a set of unique questions"""

    i = 0
    qa_chunks_str = ""
    deduplicated_qa_set = {
        "questions":[],
        "answers": []
    }
    print(f"\n\nGenerating questions for {persona} with {perspective} perspective\n\n")
    print(f"\n\n")
    print(qa_sets)
    print(f"\n\n")
    print(len(qa_sets))

    # Create N chunks of at most MAK_TOKENS_SIZE
    while i < len(qa_sets):

        # Deduplicate questions

        chunk_str = f"\n<qa_set_chunk_{i}> \n{qa_sets[i]}\n </qa_set_chunk_{i}>\n"
        print("\n\nChunk len\n\n")
        print(len(chunk_str.split(" ")))

        if (len(qa_chunks_str.split(" ")) + len(chunk_str.split(" "))) < MAX_INPUT_TOKEN_COUNT:  #Assume 1 word = 1 token
            qa_chunks_str = qa_chunks_str + chunk_str
        else:

            print(f"\n\nConcatenated {i} chunks\n\n")
            print(qa_chunks_str)
            print(len(qa_chunks_str.split(" ")))

            qa_completion = generate_unique_questions_from_chunks(
                persona=persona,
                perspective=perspective,
                qa_chunks_str=qa_chunks_str
            )

            # Create QA structured set

            structured_qa = generate_structured_qa_set(qa_completion)
            print("\n\n Structured QA\n\n")
            print(structured_qa)
            deduplicated_qa_set['questions'].extend(structured_qa.questions)
            deduplicated_qa_set['answers'].extend(structured_qa.answers)

            qa_chunks_str = chunk_str

        i = i+1

    return deduplicated_qa_set

def handler(event, context):
    """
    Lambda function to extract metadata from document
    Lambda function to chunk a multipage text document
    @param event:
    @param context:
    @return:
    """

    document_key = event[0]["document_key"]
    document_name = event[0]["document_name"]

    logger.info(f"Received event: {event}")

    #doc_qa_pairs = {}
    qa_by_personna_perspective = {}

    try:

        qa_pairs = read_qa_from_s3(document_key, len(event))

        print("QA Pairs")
        print(qa_pairs)

        # loop through the results and get all questions per persona and perspective
        for element in qa_pairs:
            for persona in element:
                if persona not in qa_by_personna_perspective:
                    qa_by_personna_perspective[persona] = {}

                for perspective in element[persona]:
                    if perspective not in qa_by_personna_perspective[persona]:
                        qa_by_personna_perspective[persona][perspective] = []

                    qa_by_personna_perspective[persona][perspective].extend(element[persona][perspective]["qa_pairs"])
    except Exception as e:
        logger.error(f"Error preparing to process questions: {e}")
        traceback.print_exc()
        jobsTable.update_item(
            Key={"document_key": document_key},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": IndexingStatusEnum.ERROR.name},
        )
        raise

    try:
        #Generate structured output from questions

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(qa_by_personna_perspective, temp_file)
            qaFilename = temp_file.name

        s3.upload_file(qaFilename, DOCUMENTS_BUCKET_NAME, f'qa/{document_key}/qa_doc.json')
        
        # Clean up temp file
        if os.path.exists(qaFilename):
            os.unlink(qaFilename)

    except Exception as e:
        logger.error(f"Error storing QA: {e}")
        traceback.print_exc()
        jobsTable.update_item(
            Key={"document_key": document_key},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": IndexingStatusEnum.ERROR.name},
        )
        raise (e)

    # Update job status in DynamoDB table
    try:

        jobsTable.update_item(
            Key={"document_key": document_key},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": IndexingStatusEnum.QA_CONSOLIDATION.name},
        )

    except Exception as e:

        logger.error(f"Error updating DynamoDB: {e}")
        traceback.print_exc()
        raise(e)

    return {
        "statusCode": 200,
        "document_key": document_key,
        "document_name": document_name
    }