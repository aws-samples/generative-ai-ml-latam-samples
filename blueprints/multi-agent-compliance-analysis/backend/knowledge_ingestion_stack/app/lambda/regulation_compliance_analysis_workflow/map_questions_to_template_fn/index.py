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
import pydantic
import traceback
import tempfile

import boto3
import functools
import langchain_core

from langchain_aws import ChatBedrockConverse

from retrying import retry

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger

from botocore.exceptions import ClientError
from botocore.config import Config

from prompts.generate_questions_layout_prompt import get_questions_layout_map_prompt_selector

from status_info_layer.StatusEnum import ComplianceReportStatusEnum
from structured_output.report_layout import ComplianceReport

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
COMPLIANCE_JOBS_DYNAMODB_TABLE_NAME = os.environ.get("COMPLIANCE_JOBS_DYNAMODB_TABLE_NAME")
COMPLIANCE_REPORTS_BUCKET_NAME = os.environ.get("COMPLIANCE_REPORTS_BUCKET_NAME")

compliance_job_table = boto3.resource("dynamodb").Table(COMPLIANCE_JOBS_DYNAMODB_TABLE_NAME)
s3_client = boto3.client("s3")

STRUCTURED_OUTPUT_MODEL_TEMP = 0.3

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

# TODO: use aws_lambda_powertools.event_handler import APIGatewayRestResolver and CORSConfig to avoid having to
#  know about API GW response formats
def _format_response(handler):
    @functools.wraps(handler)
    def wrapper(event, context):
        response = handler(event, context)
        return {
            "statusCode": response["statusCode"],
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

def get_analysis_job_details(
        analysis_job_id: str
):
    """
    Given an analysis job id, obtain its details
    @param analysis_job_id
    @return:
    """

    try:
        response = compliance_job_table.get_item(
            Key={
                "job_id": analysis_job_id
            }
        )

        if "Item" in response:
            return response["Item"]
        else:
            return ""
    except ClientError as ex:
        logger.error(f"Job {analysis_job_id} does not exist")
        raise ex


# A function to generate questions from the document
@retry(wait_exponential_multiplier=10000, wait_exponential_max=240000, stop_max_attempt_number=4,
       retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
def generate_compliance_analysis_layout(
        country: str,
        industry: str,
        workload: str,
        template_layout: str,
        questions: str,
):

    global STRUCTURED_OUTPUT_MODEL_TEMP

    print("All questions")
    print(questions)

    print("Layout")
    print(template_layout)

    print("With model")
    print(MODEL_ID)

    questions_mapping_llm = ChatBedrockConverse(
        model=MODEL_ID,
        temperature=STRUCTURED_OUTPUT_MODEL_TEMP,
        max_tokens=5000,
        top_p=0.9
        # other params...
    )

    ############----------Chain action---------############
    LLM_QUESTION_LAYOUT_MAP_QUESTIONS_PROMPT_SELECTOR = get_questions_layout_map_prompt_selector(lang="en")
    question_layout_map_prompt = LLM_QUESTION_LAYOUT_MAP_QUESTIONS_PROMPT_SELECTOR.get_prompt(MODEL_ID)
    question_layout_map_chain = question_layout_map_prompt | questions_mapping_llm.with_structured_output(ComplianceReport)
    #question_layout_map_chain = question_layout_map_prompt | questions_mapping_llm

    try:

        print("\n\nGenerating mapping\n\n")
        report_sections = question_layout_map_chain.invoke(
            {
                "industry": industry,
                "country": country,
                "workload": workload,
                "questions": questions,
                "json_report_layout": template_layout
            }
        )

        print("\n\nGenerated mapping\n\n")
        print(report_sections)

        return report_sections
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
    question_subset = []
    question_layouts = []
    max_token_count = 500
    token_estimate = 0

    logger.info(f"Received event: {event}")

    #Retrieve main job id
    analysis_job_id = event["job_id"]
    report_template = event["report_template"]
    questions = event["question_set"]
    chunk_index = event["question_chunk_index"]

    logger.info(f"Document ID: {analysis_job_id}")

    try:

        #Retrieve compliance job details
        analysis_job_details = get_analysis_job_details(analysis_job_id)
        workload = analysis_job_details["workload"]
        country = analysis_job_details["country"]
        industry = analysis_job_details["industry"]

        logger.debug(f"Mapping questions to sections for {analysis_job_id} compliance job")
        logger.debug(questions)
        logger.debug(report_template)

        print("\n\nGenerating layout for questions\n\n")
        print(questions)
        print("\n\n\n\n")
    except Exception as e:
        logger.error(f"Error getting analysis details: {e}")
        compliance_job_table.update_item(
            Key={"job_id": analysis_job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": ComplianceReportStatusEnum.ERROR.name},
        )
        return {
            "statusCode": 500,
            "error": "Error getting analysis details"
        }

    try:

        report_question_layout_mapping = generate_compliance_analysis_layout(
            country = country,
            industry = industry,
            workload = workload,
            template_layout = report_template,
            questions = questions,
        )

        print("The layout mapping")
        print(report_question_layout_mapping)

    except Exception as e:
        logger.error(f"Error mapping questions to template: {e}")
        traceback.print_exc()
        compliance_job_table.update_item(
            Key={"job_id": analysis_job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": ComplianceReportStatusEnum.ERROR.name},
        )
        raise (e)

    #Push questions to S3
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        json_report_map = report_question_layout_mapping.model_dump()

        logger.debug(f"json map for chunk {chunk_index}")
        logger.debug(json_report_map)

        json.dump(json_report_map, temp_file)
        temp_filename = temp_file.name

    try:
        s3_client.upload_file(temp_filename, COMPLIANCE_REPORTS_BUCKET_NAME,
                              f'{analysis_job_id}/chunks/question_chunk_{chunk_index}.json')
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)

    # Update job status in DynamoDB table
    try:

        compliance_job_table.update_item(
            Key={"job_id": analysis_job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": ComplianceReportStatusEnum.STRUCTURING.name},
        )

    except Exception as e:
        logger.error(f"Error updating DynamoDB: {e}")
        traceback.print_exc()
        raise (e)

    return {
        "statusCode": 200,
        "job_id": analysis_job_id,
        "body": {
            "report_template": report_template
        }
    }
