# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import logging
import json
import boto3

from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

lambda_response = {
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": True,
    },
    "body": {},
}

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL"))

CAMPAIGN_TABLE_NAME = os.getenv("CAMPAIGN_TABLE_NAME")
HISTORIC_TABLE_NAME = os.getenv("HISTORIC_TABLE_NAME")
OSS_HOST = os.getenv("OSS_HOST").replace("https://", "")
OSS_EMBEDDINGS_INDEX_NAME = os.getenv("OSS_EMBEDDINGS_INDEX_NAME")
REGION = os.getenv("REGION")

campaignTable = boto3.resource("dynamodb").Table(CAMPAIGN_TABLE_NAME)
historicTable = boto3.resource("dynamodb").Table(HISTORIC_TABLE_NAME)

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=REGION
)

oss_client = boto3.client('opensearchserverless')

def encode_description(img_description: str = None, # Max 77 characters
                    dimension: int = 1024,  # 1,024 (default), 384, 256
                    model_id: str = "amazon.titan-embed-image-v1"
                    ):
    "Get text embedding using multimodal embeddings model"

    payload_body = {}
    embedding_config = {
        "embeddingConfig": {
            "outputEmbeddingLength": dimension
        }
    }

    payload_body["inputText"] = img_description

    logger.debug("embedding text")
    logger.debug(payload_body)

    response = bedrock_runtime.invoke_model(
        body=json.dumps({**payload_body, **embedding_config}),
        modelId=model_id,
        accept="application/json",
        contentType="application/json"
    )

    feature_vector = json.loads(response.get("body").read())['embedding']

    logger.debug("text embedding")
    logger.debug(feature_vector)

    return feature_vector


def search_images(index_name, embedding, oss_client, node, objective, k=3):
    matched_images = []

    body = {
        "size": k,
        "_source": {
            "exclude": ["embeddings"],
        },
        "query":
            {
                "knn":
                    {
                        "embeddings": {
                            "vector": embedding,
                            "k": k,
                        }
                    }
            },
        "post_filter": {
            "bool": {
                "filter": [
                    {"term": {"node": node}},
                    {"term": {"objective": objective}}
                ]
            }
        }
    }

    res = oss_client.search(index=index_name, body=body)

    logger.debug("The results")
    logger.debug(res)

    for hit in res["hits"]["hits"]:
        matched_images.append((hit["_source"]["results"], hit["_source"]["image_s3_uri"], hit["_source"]["img_element_list"], hit["_source"]["image_description"]))

    return matched_images


def handler(event, context):
    logger.debug("Received event: ")
    logger.debug(event)

    method = event["httpMethod"]
    uid = event["uid"]

    if method != "POST":
        lambda_response["statusCode"] = 400
        lambda_response["body"]["message"] = "Bad Request. Malformed URL"

        return lambda_response

    logger.debug("Searching campaign")

    ans = campaignTable.get_item(Key={'id':uid})
    logger.debug(ans)
    if 'Item' in ans:
        campaign = ans['Item']
    else:
        lambda_response["statusCode"] = 400
        lambda_response["body"]["message"] = "Campaign not found"

        return lambda_response

    logger.debug("Retrieved campaign: ")
    logger.debug(campaign)
    
    # Get attributes for campaign
    campaign_description = campaign['campaign_description']
    visual_concept = campaign['visual_concept']
    image_description = campaign['image_description']
    node = campaign['node']
    objective = campaign['objective']
    #result = campaign['result']

    ############ Search images related to the description ############

    logger.debug("Retrieving related images")

    # Create the OpenSearch client
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, REGION, 'aoss')

    oss_client = OpenSearch(
        hosts=[{'host': OSS_HOST, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300
    )

    logger.debug("Embedding image description")

    #Embed img description
    #TODO: Investigate if the visual concept or the image description are better to perform the search of the images
    img_desc_embedding = encode_description(image_description)
    #img_desc_embedding = encode_description(visual_concept)

    #Search for the images that match the criteria
    matched_images = search_images(OSS_EMBEDDINGS_INDEX_NAME, img_desc_embedding, oss_client, node, objective, k=5)

    logger.debug("Retrieved images")
    logger.debug(matched_images)

    if len(matched_images) == 0:
        # No matching images

        campaign["image_references"] = []
        campaignTable.put_item(Item=campaign)

        lambda_response["statusCode"] = 200
        lambda_response["body"] = []

    else:
        #Sort images based on result score
        matched_images.sort(key=lambda x: -x[0])
        
        matched_images_map = {}
        for i in matched_images:
          matched_images_map[i[1]] = i
        answer = [{"url": matched_images_map[key][1], "metric": objective, "score": matched_images_map[key][0],
                   "description": matched_images_map[key][3], "img_elements":matched_images_map[key][2]} for key in
                  matched_images_map]

        #Update dynamo table
        campaign["image_references"] = answer
        campaignTable.put_item(Item=campaign)

        lambda_response["statusCode"] = 200
        lambda_response["body"] = json.dumps(answer)

    return lambda_response
