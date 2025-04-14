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
import urllib.parse

import boto3
import cfnresponse
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

tracer = Tracer()
logger = Logger()

client = boto3.client('opensearchserverless')

@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def handler(event, context: LambdaContext):
    request_type = event["RequestType"]
    resource_properties = event["ResourceProperties"]

    logger.info(request_type)
    logger.info(resource_properties)

    service = 'aoss'

    # Mandatory properties
    index_name = resource_properties["IndexName"]
    endpoint = resource_properties["Endpoint"]
    region = resource_properties["Region"]

    host = urllib.parse.urlparse(endpoint).hostname
    print(endpoint)
    print(host)

    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, region, service)

    oss_client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300
    )

    if request_type == "Create":
        logger.info(f"Creating index {index_name}")
        try:
            create_index(
                oss_client,
                index_name,
            )
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {"ok": True})
        except Exception as e:
            logger.error(e)
            error = f"Error creating index {index_name}: {e}"
            logger.error(error)
            cfnresponse.send(
                event, context, cfnresponse.FAILED, {"ok": False, "error": error}
            )
            raise e

    elif request_type == "Update":
        logger.info(f"Updating index {index_name}")
        try:
            delete_index(oss_client, index_name)
            create_index(
                oss_client,
                index_name,
            )
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {"ok": True})
        except Exception as e:
            logger.error(e)
            error = f"Error updating index {index_name}: {e}"
            logger.error(error)
            cfnresponse.send(
                event, context, cfnresponse.FAILED, {"ok": False, "error": error}
            )
            raise e

    elif request_type == "Delete":
        logger.info(f"Deleting index {index_name}")
        try:
            delete_index(oss_client, index_name)
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {"ok": True})
        except Exception as e:
            logger.error(e)
            error = f"Error deleting index {index_name}: {e}"
            logger.error(error)
            cfnresponse.send(
                event, context, cfnresponse.FAILED, {"ok": False, "error": error}
            )
            raise e

    else:
        error = f"Unknown request type {request_type}"
        logger.error(error)
        cfnresponse.send(
            event, context, cfnresponse.FAILED, {"ok": False, "error": error}
        )
        raise Exception(error)


def create_index(
    opensearch,
    index_name,
):
    index_body = {
        "mappings": {
            "properties": {
                "results": {"type": "float"},
                "node": {"type": "keyword"},
                "objective": {"type": "keyword"},
                "image_s3_uri": {"type": "text"},
                "image_description": {"type": "text"},
                "img_element_list": {"type": "text"},
                "embeddings": {
                    "type": "knn_vector",
                    "dimension": 1024,
                    "method": {
                        "engine": "nmslib",
                        "space_type": "cosinesimil",
                        "name": "hnsw",
                        "parameters": {"ef_construction": 512, "m": 16}
                    }
                }
            }
        },
        "settings": {
            "index": {
                "number_of_shards": 2,
                "knn.algo_param": {"ef_search": 512},
                "knn": True
            }
        }
    }

    logger.info(f"Creating index {index_name} with body:")
    logger.info(index_body)

    response = opensearch.indices.create(index_name, body=index_body)
    logger.info("The response")
    logger.info(response)


def delete_index(opensearch, index_name):
    response = opensearch.indices.delete(index_name)
    logger.info(response)