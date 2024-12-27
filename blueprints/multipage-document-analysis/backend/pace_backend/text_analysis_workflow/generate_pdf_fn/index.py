# MIT No Attribution
#
# Copyright 2024 Amazon Web Services
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

import tempfile
import os
import boto3
import json
import uuid

import functools

from pydantic import TypeAdapter
from fpdf import FPDF

from doc_info_layer.section_definition import info_to_output_mapping, report_sections

from status_info_layer.StatusEnum import StatusEnum

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

S3_BUCKET = os.getenv("OUTPUT_BUCKET_NAME")
TABLE_NAME = os.getenv("DOCUMENTS_DYNAMO_DB_TABLE_NAME")
REGION = os.getenv("REGION")

table = boto3.resource("dynamodb").Table(TABLE_NAME)
s3 = boto3.client('s3')

def get_item_by_id(id: str):
    item = table.get_item(Key={"id": id})
    if "Item" not in item:
        raise KeyError("Item not found")
    return json.loads(item["Item"]["json_report"])

def create_pdf(report):
    ### Create PDF

    pdf = FPDF()
    pdf.set_font("Times", size=16)

    pdf.add_page()

    pdf.cell(200, 10, txt="Resumen de Documento", ln=1, align="C")

    ### Create section table
    for i, section in zip(range(len(report_sections)), report_sections):
        if section in report.keys():

            pdf.cell(200, 10, txt="", ln=1, align="C")

            logger.info(f"Creating section {section}")
            logger.info(report[section])

            pydantic_section = TypeAdapter(info_to_output_mapping[section]).validate_python(report[section])

            section_tuples = pydantic_section.to_tuples_table()

            logger.info(f"Section tuples {section}")
            logger.info(section_tuples)

            with pdf.table() as table:
                for data_row in section_tuples:
                    row = table.row()
                    for datum in data_row:
                        row.cell(datum)

            if i < len(report_sections) - 1:
                pdf.add_page()

    return pdf

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

@_format_response
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, _context: LambdaContext):
    logger.info(f'Got the following event {event}')
    logger.info(event)

    filename = "document_report.pdf"

    id = str(uuid.uuid4())
    s3_key = f"{id}/{filename}"

    job_id = event["Payload"]["body"]["job_id"]

    doc_report = get_item_by_id(job_id)

    logger.info("Creating PDF for")
    logger.info(doc_report)

    report_pdf = create_pdf(doc_report)

    #Save a file to the lambda local filesystem
    tmpdir = tempfile.mkdtemp()
    tmpfile_path = os.path.join(tmpdir,filename)
    report_pdf.output(tmpfile_path)

    #Upload the file to S3
    s3.upload_file(tmpfile_path, S3_BUCKET, s3_key)

    # Update status in DynamoDB table
    try:
        table.update_item(
            Key={"id": job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": StatusEnum.PDF_GENERATION.name},
        )

        table.update_item(
            Key={"id": job_id},
            UpdateExpression="SET #report_key = :report_key",
            ExpressionAttributeNames={"#report_key": "report_key"},
            ExpressionAttributeValues={":report_key": s3_key},
        )
    except Exception as e:
        logger.error(f"Error updating DynamoDB: {e}")
        return {
            "statusCode": 500,
            "error": "Failed to update DynamoDB"
        }

    return {
        "statusCode": 200,
        "body": {
            "job_id": job_id,
            "s3_key": s3_key
        }
    }


