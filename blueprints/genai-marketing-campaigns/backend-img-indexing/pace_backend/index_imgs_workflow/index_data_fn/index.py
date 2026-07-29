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
import os
import logging

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL"))

IMG_BUCKET = os.getenv("IMG_BUCKET")
VECTOR_BUCKET_NAME = os.getenv("VECTOR_BUCKET_NAME")
VECTOR_INDEX_NAME = os.getenv("VECTOR_INDEX_NAME")
REGION = os.getenv("REGION") or boto3.session.Session().region_name

s3vectors_client = boto3.client("s3vectors", region_name=REGION)

lambda_response = {
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": True,
    },
    "body": {},
}

def lambda_handler(event, context):

    logger.debug("Received event")
    logger.debug(event)

    try:

        photo_img_url = "s3://" + IMG_BUCKET + "/" + event['img_key']
        labels_list_str = ','.join(event['labels_list'])
        embedding = event['embeddings']
        metadata = event['metadata']

        vector = {
            "key": event['img_key'].split('/')[-1].split('.')[0],
            "data": {"float32": [float(v) for v in embedding]},
            "metadata": {
                "results": metadata['results'],
                "node": metadata['node'].lower(),
                "objective": metadata['objective'].lower(),
                "image_s3_uri": photo_img_url,
                "image_description": event["img_desc"],
                "img_element_list": labels_list_str,
            },
        }

        s3vectors_response = s3vectors_client.put_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            vectors=[vector],
        )

        logger.debug(s3vectors_response)

        lambda_response['statusCode'] = 201
        lambda_response['body']['msg'] = 'Successfully added img to vector index'

    except  Exception as e:
        logger.error(e)

        lambda_response['statusCode'] = 500
        lambda_response['body']['msg'] = 'Could not add image to vector index'

        raise e

    return lambda_response
