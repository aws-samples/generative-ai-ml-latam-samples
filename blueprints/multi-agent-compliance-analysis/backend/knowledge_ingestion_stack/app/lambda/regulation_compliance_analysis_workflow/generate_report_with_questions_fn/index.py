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
import tempfile

import boto3
import functools
import traceback
import heapq

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger

from status_info_layer.StatusEnum import ComplianceReportStatusEnum

logger = Logger()

AWS_REGION = os.environ.get("REGION")
COMPLIANCE_JOBS_DYNAMODB_TABLE_NAME = os.environ.get("COMPLIANCE_JOBS_DYNAMODB_TABLE_NAME")
COMPLIANCE_REPORTS_BUCKET_NAME = os.environ.get("COMPLIANCE_REPORTS_BUCKET_NAME")

compliance_job_table = boto3.resource("dynamodb").Table(COMPLIANCE_JOBS_DYNAMODB_TABLE_NAME)
s3_client = boto3.client("s3")

def heapsort(iterable):
    h = []
    for value in iterable:
        heapq.heappush(h, value)
    return [heapq.heappop(h) for i in range(len(h))]

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


def read_questions_template_from_s3(
        job_id,
        n_chunks
):

    questions_report = []

    # Download file from S3
    print(f"Downloading files from S3: {COMPLIANCE_REPORTS_BUCKET_NAME}/{job_id}")

    for i in range(n_chunks):
        chunk_s3_key = f'{job_id}/chunks/question_chunk_{i}.json'
        
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
            local_filename = temp_file.name
        
        try:
            s3_client.download_file(COMPLIANCE_REPORTS_BUCKET_NAME, chunk_s3_key, local_filename)

            with open(local_filename) as f:
                questions_report.append(json.load(f))
                print(questions_report)
        finally:
            # Clean up the temporary file
            if os.path.exists(local_filename):
                os.unlink(local_filename)

    return questions_report

@_format_response
@logger.inject_lambda_context(log_event=True)
def handler(event, _context: LambdaContext):
    """
    Lambda function to create multiple perspectives per chunk
    @param event:
    @param context:
    @return:
    """

    unified_report_template = {}

    logger.info(f"Received event: {event}")

    #Retrieve main job id
    analysis_job_id = event[0]["job_id"]
    report_empty_template = event[0]["report_template"]
    n_chunks = len(event)
    max_order_number = 0
    ordered_sections = []

    logger.info(f"Document ID: {analysis_job_id}")

    #Download report chunks from S3
    report_templates = read_questions_template_from_s3(job_id=analysis_job_id, n_chunks=n_chunks)

    try:

        logger.debug(f"Merging resulting report templates")
        logger.debug(report_templates)

        # Merge all report templates into a unified one
        for report_template in report_templates:
            sections = report_template["sections"]
            for section in sections:
                if "section_name" in section and "questions" in section:
                    if len(section["questions"]) > 0:
                        #Only process sections with questions and a description

                        if section["section_name"] in unified_report_template:
                            unified_report_template[section["section_name"]]["questions"] = section["questions"]
                        else:
                            unified_report_template[section["section_name"]] = {
                                "description": section["section_description"],
                                "questions": section["questions"],
                            }

                        if section["section_name"] in report_empty_template:
                            order_number = int(report_empty_template[section["section_name"]]["order"])
                            unified_report_template[section["section_name"]]["order"] = order_number

                            if order_number > max_order_number:
                                max_order_number = order_number

        # Fill out order number for the new sections
        for section in unified_report_template:
            if "order" not in unified_report_template[section]:
                max_order_number += 1
                unified_report_template[section]["order"] = max_order_number

            # Push every section into a heap for sorting them afterwards
            heapq.heappush(
                ordered_sections,
                (unified_report_template[section]["order"], section)
            )

        # Sort sections for re-labeling the order
        ordered_sections = heapsort(ordered_sections)

        # Re-label section order to make it start from 1 and continue
        for i, section in enumerate(ordered_sections, start=1):
            unified_report_template[section[1]]["order"] = i

        print("\n\nUnified report\n\n")
        print(unified_report_template)

    except Exception as e:
        logger.error(f"Error generating report template: {e}")
        compliance_job_table.update_item(
            Key={"job_id": analysis_job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": ComplianceReportStatusEnum.ERROR.name},
        )
        raise

    # Update job status in DynamoDB table
    try:

        compliance_job_table.update_item(
            Key={"job_id": analysis_job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": ComplianceReportStatusEnum.STRUCTURING.name},
        )

        compliance_job_table.update_item(
            Key={"job_id": analysis_job_id},
            UpdateExpression="SET #report_with_questions = :report_with_questions",
            ExpressionAttributeNames={"#report_with_questions": "report_with_questions"},
            ExpressionAttributeValues={":report_with_questions": json.dumps(unified_report_template)},
        )

        compliance_job_table.update_item(
            Key={"job_id": analysis_job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": ComplianceReportStatusEnum.READY.name},
        )

    except Exception as e:

        logger.error(f"Error updating DynamoDB: {e}")
        traceback.print_exc()
        raise (e)

    return {
        "statusCode": 200,
        "job_id": analysis_job_id,
        "body": {
            "report_template": json.dumps(unified_report_template)
        }
    }
