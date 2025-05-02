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

import json
import boto3
import os
import json
import logging
import tempfile
import base64

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL"))

IMG_BUCKET = os.getenv("IMG_BUCKET")

REGION = os.getenv("REGION")

logger.info(f"REGION: {REGION}")

s3 = boto3.client('s3')
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=REGION
)

lambda_response = {
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": True,
    },
    "body": {},
}

def encode_image(image_path: str = None,  # maximum 2048 x 2048 pixels
            dimension: int = 1024,  # 1,024 (default), 384, 256
            model_id: str = "amazon.titan-embed-image-v1"
                 ):
    "Get img embedding using embeddings model"

    payload_body = {}
    embedding_config = {
        "embeddingConfig": {
            "outputEmbeddingLength": dimension
        }
    }

    with open(image_path, "rb") as image_file:
        input_image = base64.b64encode(image_file.read()).decode('utf8')
    payload_body["inputImage"] = input_image

    logger.debug("embedding image")
    logger.debug(payload_body)

    response = bedrock_runtime.invoke_model(
        body=json.dumps({**payload_body, **embedding_config}),
        modelId=model_id,
        accept="application/json",
        contentType="application/json"
    )

    feature_vector = json.loads(response.get("body").read())

    logger.debug("img embedding")
    logger.debug(feature_vector)

    return feature_vector

def lambda_handler(event, context):

    img_key = event["img_key"]

    try:
      
        tmp_file = tempfile.mkdtemp() + '/img.jpg'
        with open(tmp_file , 'wb') as f:
            s3.download_fileobj(IMG_BUCKET, img_key, f)

        feature_vector = encode_image(image_path=tmp_file, dimension=1024)

        lambda_response['statusCode'] = 201
        lambda_response['body']['embedding'] = feature_vector
        lambda_response['body']['msg'] = 'success'

    except Exception as e:
        logger.error(e)

        lambda_response['statusCode'] = 500
        lambda_response['body']['msg'] = 'Could not get image embeddings'

        raise e


    return lambda_response