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

import os
import json

import boto3
import functools
import traceback

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger

from botocore.exceptions import ClientError

from status_info_layer.StatusEnum import ComplianceReportStatusEnum, QuestionStatusEnum

logger = Logger()

AWS_REGION = os.environ.get("REGION")
LANGUAGE_ID = os.environ.get("LANGUAGE_ID")
QUESTION_JOBS_DYNAMODB_TABLE_NAME = os.environ.get("QUESTION_JOBS_DYNAMODB_TABLE_NAME")
COMPLIANCE_JOBS_DYNAMODB_TABLE_NAME = os.environ.get("COMPLIANCE_JOBS_DYNAMODB_TABLE_NAME")
MAX_QUESTIONS_TOKEN_COUNT = int(os.environ.get("MAX_QUESTIONS_TOKEN_COUNT"))

compliance_job_table = boto3.resource("dynamodb").Table(COMPLIANCE_JOBS_DYNAMODB_TABLE_NAME)
questions_job_table = boto3.resource("dynamodb").Table(QUESTION_JOBS_DYNAMODB_TABLE_NAME)

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


def get_questions_for_analysis_job(
        analysis_job_id: str
):
    """
    Get the question jobs part of this analysis job
    @param main_job_id:
    @return:
    """

    questions = []
    try:

        #Given a value  for the main_job_id, get all the question jobs that have the same main_job_id
        response = questions_job_table.query(
            IndexName="QuestionsByAnalysisId",
            KeyConditionExpression="main_job_id = :main_job_id",
            ExpressionAttributeValues={
                ":main_job_id": analysis_job_id
            }
        )
        print(response)

        if "Items" in response:
            items = response["Items"]

            for item in items:
                print(item)
                if item["status"] == QuestionStatusEnum.SUCCESS.name:
                    questions.extend(json.loads(item["questions"]))

            return questions
        else:
            return ""
    except ClientError as ex:
        logger.error(f"Job {analysis_job_id} does not exist")
        raise ex

@_format_response
@logger.inject_lambda_context(log_event=True)
def handler(event, _context: LambdaContext):
    """
    Lambda function to create multiple perspectives per chunk
    @param event:
    @param context:
    @return:
    """

    question_chunks = []
    question_subset = []
    max_token_count = MAX_QUESTIONS_TOKEN_COUNT
    token_estimate = 0

    logger.info(f"Received event: {event}")

    #Retrieve main job id
    analysis_job_id = event["job_id"]
    report_template = event["report_template"]

    try:

        logger.debug(f"Document ID: {analysis_job_id}")
        questions = get_questions_for_analysis_job(analysis_job_id)

        logger.debug(f"Mapping questions to sections for {analysis_job_id} compliance job")
        logger.debug(questions)
        logger.debug(report_template)

        # Split all questions into sets more manageable by the LLM
        for question in questions:
            token_estimate += len(question.split(" "))*4/3

            print(token_estimate)

            if token_estimate < max_token_count:
                question_subset.append(question)
            else:
                print(f"\n\nTotal number of questions: {len(question_subset)}")
                question_chunks.append('\n'.join(question_subset))
                question_subset = []
                token_estimate = 0

        print("\n\nQuestion aggregates\n\n")
        print(len(question_chunks))
        print(question_chunks)

    except Exception as e:
        logger.error(f"Error splitting questions: {e}")
        compliance_job_table.update_item(
            Key={"job_id": analysis_job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": ComplianceReportStatusEnum.ERROR.name},
        )
        return {
            "statusCode": 500,
            "error": "Error downloading QA document"
        }

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
            "question_chunks": question_chunks,
            "report_template": report_template
        }
    }
