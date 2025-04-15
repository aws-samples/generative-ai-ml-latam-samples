# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import os
import logging

from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL"))

IMG_BUCKET = os.getenv("IMG_BUCKET")

client = boto3.client('opensearchserverless')
region = boto3.session.Session().region_name
service = 'aoss'

OSS_HOST = os.getenv("OSS_HOST").replace("https://", "")
OSS_EMBEDDINGS_INDEX_NAME = os.getenv("OSS_EMBEDDINGS_INDEX_NAME")

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

        document = {
            "id": event['img_key'].split('/')[-1].split('.')[0],
            "results": metadata['results'],
            "node": metadata['node'].lower(),
            "objective":  metadata['objective'].lower(),
            "image_s3_uri": photo_img_url,
            "image_description": event["img_desc"],
            "img_element_list": labels_list_str,
            "embeddings": embedding
        }

        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, region, service)

        # Build the OpenSearch client
        oss_client = OpenSearch(
            hosts=[{'host': OSS_HOST, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=300
        )

        oss_response = oss_client.index(
            index=OSS_EMBEDDINGS_INDEX_NAME,
            body=document,
        )

        lambda_response['statusCode'] = 201
        lambda_response['body']['msg'] = 'Successfully added img to oss index'

    except  Exception as e:
        logger.error(e)

        lambda_response['statusCode'] = 500
        lambda_response['body']['msg'] = 'Could not add image to oss index'

        raise e

    return lambda_response