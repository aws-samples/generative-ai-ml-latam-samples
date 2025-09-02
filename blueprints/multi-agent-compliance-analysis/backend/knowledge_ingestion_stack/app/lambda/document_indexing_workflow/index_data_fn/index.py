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
import datetime
import json
import os
import functools
import traceback
import tempfile

from retrying import retry

from aws_lambda_powertools import Logger

from botocore.exceptions import ClientError
from botocore.config import Config

from status_info_layer.StatusEnum import IndexingStatusEnum

from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

class BedrockRetryableError(Exception):
    """Class to identify a Bedrock throttling error"""

    def __init__(self, msg):
        super().__init__(self)

        self.message = msg

logger = Logger()

REGION = os.environ.get("REGION")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID")
LANGUAGE_ID = os.environ.get("LANGUAGE_ID")
JOBS_DYNAMODB_TABLE_NAME = os.environ.get("JOBS_DYNAMO_DB_TABLE_NAME")
OSS_HOST = os.getenv("OSS_HOST").replace("https://", "")
OSS_EMBEDDINGS_INDEX_NAME = os.getenv("OSS_EMBEDDINGS_INDEX_NAME")
DOCUMENTS_BUCKET_NAME = os.environ.get("DOCUMENT_BUCKET_NAME")

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=BEDROCK_REGION,
    config=Config(retries={'max_attempts': 20})
)
s3 = boto3.client('s3')

client = boto3.client('opensearchserverless')
service = 'aoss'

credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, REGION, service)

# Build the OpenSearch client
oss_client = OpenSearch(
    hosts=[{'host': OSS_HOST, 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=300
)

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

# A function to encode text into a vector
@retry(wait_exponential_multiplier=10000, wait_exponential_max=60000, stop_max_attempt_number=10,
       retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
def encode_text(
        text: str = None,  # the text to be encoded
        dimension: int = 1024,  # 1,024 (default), 384, 256
):
    "Get text embedding using embeddings model"

    payload_body = {
        "inputText": text,
        "dimensions": dimension,
        "normalize": True
    }

    logger.debug("embedding text")
    logger.debug(payload_body)

    response = bedrock_runtime.invoke_model(
        body=json.dumps(payload_body),
        modelId=MODEL_ID,
        accept="application/json",
        contentType="application/json"
    )

    feature_vector = json.loads(response.get("body").read())["embedding"]

    logger.debug("text embedding")
    logger.debug(feature_vector)

    return feature_vector


def index_document(
        embedding,
        document_key,
        document_version,
        persona,
        perspective,
        question,
        answer
):
    # Index a document into Amazon Open Search Serverless

    document = {
        "persona": persona,
        "perspective": perspective,
        "doc_version": document_version if document_version else "",
        "doc_key": document_key,
        "question": question,
        "answer": answer,
        "embedding": embedding
    }

    oss_response = oss_client.index(
        index=OSS_EMBEDDINGS_INDEX_NAME,
        body=document,
    )

    return oss_response


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

    try:
        # Download file from S3
        print(f"Downloading file from S3: {DOCUMENTS_BUCKET_NAME}/{document_key}")
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
            local_filename = temp_file.name
        
        s3.download_file(DOCUMENTS_BUCKET_NAME, os.path.join("qa", document_key, "qa_doc.json"), local_filename)

        with open(local_filename, 'r') as f:
            qa_pairs = json.load(f)
        
        # Clean up the temporary file
        if os.path.exists(local_filename):
            os.unlink(local_filename)
    except Exception as e:
        logger.error(f"Error downloading QA document: {e}")
        jobsTable.update_item(
            Key={"document_key": document_key},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": IndexingStatusEnum.ERROR.name},
        )
        raise

    # Encode text and index it
    try:
        for persona in qa_pairs:
            for perspective in qa_pairs[persona]:
                for qa_pair in qa_pairs[persona][perspective]:

                    question = qa_pair["question"]
                    answer = qa_pair["answer"]

                    logger.info(f"Q&A pair:\n\n{question}\n{answer}")
                    question_vector = encode_text(question)

                    #Index Q&A pair
                    oss_response = index_document(
                        embedding=question_vector,
                        document_key=document_key,
                        document_version=metadata["document_version"],
                        persona=persona,
                        perspective=perspective,
                        question=question,
                        answer=answer
                    )

                    logger.info(f"Q&A pair indexed: {oss_response}")

    except Exception as e:
        logger.error(f"Error indexing questions: {e}")
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
            ExpressionAttributeValues={":status": IndexingStatusEnum.DATA_INDEXING.name},
        )

        jobsTable.update_item(
            Key={"document_key": document_key},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": IndexingStatusEnum.SUCCESS.name},
        )

    except Exception as e:
        logger.error(f"Error updating DynamoDB: {e}")
        traceback.print_exc()
        raise (e)

    return {
        "statusCode": 200,
    }