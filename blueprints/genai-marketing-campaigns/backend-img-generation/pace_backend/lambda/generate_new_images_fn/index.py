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
import base64
import io
import uuid
import tempfile
import json

import boto3
from PIL import Image
import random

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
campaignTable = boto3.resource("dynamodb").Table(CAMPAIGN_TABLE_NAME)

PROCESSED_BUCKET = os.getenv("PROCESSED_BUCKET")
REGION = os.getenv("REGION")
MODEL_ID = os.getenv("IMG_MODEL_ID")
# Provider selects the invoke-body/response adapter. Defaults to "stability"
# (Nova Canvas reached Bedrock EOL 2026-09-30). Kept as a config knob so a
# future model swap is an env change, not a code change.
IMG_PROVIDER = os.getenv("IMG_PROVIDER", "stability")
# Aspect ratio replaces Nova's pixel dims. "16:9" matches the original 1280x720 intent.
IMG_ASPECT_RATIO = os.getenv("IMG_ASPECT_RATIO", "16:9")

logger.info(f"REGION: {REGION} | MODEL_ID: {MODEL_ID} | PROVIDER: {IMG_PROVIDER}")

s3 = boto3.resource("s3")
processed_bucket = s3.Bucket(PROCESSED_BUCKET)

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=REGION
)

NEGATIVE_PROMPTS = "poorly rendered, poor background details, poorly facial details"


class ImageFilteredError(Exception):
    """Raised when the model's content filter blocked generation (no image returned)."""


def _build_stability_body(prompt: str, seed: int) -> str:
    """Invoke body for Stability AI models (Stable Image Ultra/Core, SD3.5)."""
    return json.dumps(
        {
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPTS,  # plain keywords, no negation words
            "aspect_ratio": IMG_ASPECT_RATIO,     # replaces explicit pixel dims
            "seed": seed,
            "output_format": "jpeg",
        }
    )


def _build_nova_canvas_body(prompt: str, seed: int) -> str:
    """Invoke body for Amazon Nova Canvas (legacy; retained for fallback/parity)."""
    return json.dumps(
        {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": prompt,
                "negativeText": NEGATIVE_PROMPTS,
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "quality": "standard",
                "height": 720,
                "width": 1280,
                "cfgScale": 7.5,
                "seed": seed,
            },
        }
    )


# provider -> body builder. Both providers return the generated image(s) under
# the same "images" key, so response handling is shared below.
_BODY_BUILDERS = {
    "stability": _build_stability_body,
    "nova_canvas": _build_nova_canvas_body,
}


def genImgCanvas(prompt: str):
    """Generate an image from a prompt via the configured Bedrock image provider."""

    seed = int(random.randrange(0x0CCD569F))  # nosec B311 not being used for security
    logger.debug("seed = " + str(seed))

    build_body = _BODY_BUILDERS.get(IMG_PROVIDER)
    if build_body is None:
        raise ValueError(f"Unsupported IMG_PROVIDER: {IMG_PROVIDER}")

    body = build_body(prompt, seed)

    response = bedrock_runtime.invoke_model(
        body=body,
        modelId=MODEL_ID,
        accept="application/json",
        contentType="application/json"
    )
    response_body = json.loads(response.get("body").read())

    # Stability omits "images" and returns "finish_reasons" when a prompt is
    # blocked by the content filter. Nova returned an image unconditionally, so
    # this guard is new and required for the migration.
    images = response_body.get("images")
    if not images:
        finish_reasons = response_body.get("finish_reasons") or response_body.get("finish_reason")
        logger.warning(f"No image returned. finish_reasons={finish_reasons}")
        raise ImageFilteredError(
            "The prompt was blocked by the model's content filter. "
            "Please adjust the campaign description and try again."
        )

    base_64_img_str = images[0]

    tmpdir = tempfile.mkdtemp()
    image_file = str(uuid.uuid4()) + ".jpg"
    image_path = tmpdir + "/" + image_file
    image_1 = Image.open(io.BytesIO(base64.decodebytes(bytes(base_64_img_str, "utf-8"))))

    # save
    image_1.save(image_path)
    return image_path, image_file

def handler(event, context):
    logger.debug("Received event: " + json.dumps(event))
    method = event["httpMethod"]
    path = event["path"]
    pathParts = path.split('/')

    if method != "POST" or len(pathParts) != 3 or pathParts[1] != "generate_images":

        lambda_response["statusCode"] = 400
        lambda_response["body"]["message"] = "Bad Request. Malformed URL"

        return lambda_response

    uid = pathParts[-1]

    # Get attributes for campaign

    try:
        body = json.loads(event["body"])
        prompt = body["prompt"]
    except:
        lambda_response["statusCode"] = 400
        lambda_response["body"]["message"] = "Bad Request. Bad body"

        return lambda_response

    #Generate an image based on the prompt
    try:
        image_path, image_file = genImgCanvas(prompt)
    except ImageFilteredError as e:
        lambda_response["statusCode"] = 400
        lambda_response["body"] = json.dumps({"message": str(e)})
        return lambda_response

    #Read dynamo table
    ans = campaignTable.get_item(Key={'id':uid})
    if 'Item' in ans:
        campaign = ans['Item']
    else:
        lambda_response["statusCode"] = 500
        lambda_response["body"]["message"] = "Campaign not found"

        return lambda_response

    fileKey = campaign["id"] + "/" + image_file
    processed_bucket.upload_file(image_path,fileKey)

    url = "s3://" + PROCESSED_BUCKET + "/" + fileKey


    #Update dynamo table
    ans = campaignTable.get_item(Key={'id':uid})
    if 'Item' in ans:
        campaign = ans['Item']
    else:
        lambda_response["statusCode"] = 500
        lambda_response["body"]["message"] = "Campaign not found"

        return lambda_response
      
    if not "generated_images" in campaign:
      campaign["generated_images"] = []
    campaign["generated_images"].append({"url":url})
    campaignTable.put_item(Item=campaign)

    lambda_response["statusCode"] = 200
    lambda_response["body"] = json.dumps({"url":url})

    return lambda_response
