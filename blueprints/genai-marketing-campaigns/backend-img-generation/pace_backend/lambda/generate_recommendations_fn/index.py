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
import logging
import json
import boto3

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
VECTOR_BUCKET_NAME = os.getenv("VECTOR_BUCKET_NAME")
VECTOR_INDEX_NAME = os.getenv("VECTOR_INDEX_NAME")
REGION = os.getenv("REGION")

campaignTable = boto3.resource("dynamodb").Table(CAMPAIGN_TABLE_NAME)
historicTable = boto3.resource("dynamodb").Table(HISTORIC_TABLE_NAME)

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=REGION
)

s3vectors_client = boto3.client("s3vectors", region_name=REGION)

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


def search_images(embedding, node, objective, k=3):
    """Query the S3 Vectors index for the k nearest images matching node/objective.

    S3 Vectors applies the metadata filter DURING the search (pre-filter), so
    topK=k returns the k nearest vectors that match node + objective — unlike
    the previous OpenSearch post_filter which could return fewer (or zero)
    matches.
    """
    matched_images = []

    res = s3vectors_client.query_vectors(
        vectorBucketName=VECTOR_BUCKET_NAME,
        indexName=VECTOR_INDEX_NAME,
        queryVector={"float32": [float(v) for v in embedding]},
        topK=k,
        filter={"$and": [{"node": {"$eq": node}}, {"objective": {"$eq": objective}}]},
        returnMetadata=True,
        returnDistance=True,
    )

    logger.debug("The results")
    logger.debug(res)

    for vector in res.get("vectors", []):
        metadata = vector.get("metadata", {})
        matched_images.append((metadata["results"], metadata["image_s3_uri"], metadata["img_element_list"], metadata["image_description"]))

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

    logger.debug("Embedding image description")

    #Embed img description
    #TODO: Investigate if the visual concept or the image description are better to perform the search of the images
    img_desc_embedding = encode_description(image_description)
    #img_desc_embedding = encode_description(visual_concept)

    #Search for the images that match the criteria
    matched_images = search_images(img_desc_embedding, node, objective, k=5)

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
