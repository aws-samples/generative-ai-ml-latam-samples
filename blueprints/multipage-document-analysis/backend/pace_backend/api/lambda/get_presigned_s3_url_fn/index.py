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

import os
import re
import functools
import json
import boto3
from botocore.client import Config
from urllib.parse import urlparse

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger

from botocore.exceptions import ClientError

REGION = os.getenv("REGION")
DOCS_BUCKET = os.getenv("DOCUMENTS_BUCKET_NAME")
REPORTS_BUCKET = os.getenv("REPORTS_BUCKET_NAME")

DOWNLOAD_REPORT_BY_ID_PATTERN = re.compile("(/[a-zA-Z0-9-]*)*/download/report/[A-Za-z0-9-]*/[A-Za-z0-9-_]*.(pdf)")
DOWNLOAD_DOCUMENT_BY_ID_PATTERN = re.compile("(/[a-zA-Z0-9-]*)*/download/document/[A-Za-z0-9-]*/[A-Za-z0-9-_]*.(pdf)")
UPLOAD_DOCUMENT_BY_ID_PATTERN = re.compile("(/[a-zA-Z0-9-]*)*/upload/[A-Za-z0-9-]*/[A-Za-z0-9-]*.(pdf)")

logger = Logger()

s3_client = boto3.client(
    "s3",
    region_name=REGION,
    config=Config
    (
        s3={'addressing_style': 'path'},
        signature_version="s3v4"
    )
)

duration = 24 * 60 * 60


# TODO: use aws_lambda_powertools.event_handler import APIGatewayRestResolver and CORSConfig to avoid having to
#  know about API GW response formats
def _format_response(handler):
    @functools.wraps(handler)
    def wrapper(event, context):
        lambda_response = handler(event, context)

        response = {
            "statusCode": lambda_response["statusCode"],
            "isBase64Encoded": False,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": "",
        }

        logger.info(lambda_response)

        if lambda_response["statusCode"] == 200:
            response["body"] = json.dumps({
                "presigned_url": lambda_response["presigned_url"],
            })
        else:
            response["body"] = json.dumps({
                "message": lambda_response["message"],
            })

        return response

    return wrapper


@_format_response
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, _context: LambdaContext):

    method = event["httpMethod"]
    path = event["path"]
    pathParts = path.split('/')[1:]

    logger.info(method)
    logger.info(path)
    logger.info(pathParts)

    lambda_response = {}

    try:

        if method == "GET" and UPLOAD_DOCUMENT_BY_ID_PATTERN.match(path):
            lambda_response["statusCode"] = 200
            lambda_response["presigned_url"] = s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": DOCS_BUCKET,
                    "Key": pathParts[2] + "/" + pathParts[3],
                },
                ExpiresIn=duration,
            )
        elif method == "GET" and DOWNLOAD_DOCUMENT_BY_ID_PATTERN.match(path):
            lambda_response["statusCode"] = 200
            lambda_response["presigned_url"] = s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": DOCS_BUCKET,
                    "Key": pathParts[3] + "/" + pathParts[4],
                },
                ExpiresIn=duration,
            )
        elif method == "GET" and DOWNLOAD_REPORT_BY_ID_PATTERN.match(path):
            lambda_response["statusCode"] = 200
            lambda_response["presigned_url"] = s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": REPORTS_BUCKET,
                    "Key": pathParts[3] + "/" + pathParts[4],
                },
                ExpiresIn=duration,
            )
        else:
            lambda_response["statusCode"] = 200
            lambda_response["message"] = "Bad Request. Malformed URL"

    except ClientError as e:
        logger.error(e)
        lambda_response["statusCode"] = 400
        lambda_response["message"] = "Bad Request. Bad body"

    return lambda_response
