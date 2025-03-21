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

import os.path
from fileinput import filename

import requests
import glob
import boto3
import time
import json
import random
import argparse

import fiftyone.zoo as foz

CampaignObjective = [
    "clicks",
    "awareness",
    "likes",
]

CampaignNode = [
    "followers",
    "customers",
    "new_customers"
]


s3 = boto3.client ('s3')

def put_img(url, local_path, filename, token):

    api_prefix = "imgMetaIndex/upload/original/"

    headers = {
        'Authorization': 'Bearer '+token,
    }

    with open(local_path, "rb") as f:
        data = f.read()

    if 'jpg' in filename or 'jpeg' in filename:
        headers['Content-Type'] = 'image/jpeg'
    elif 'png' in filename:
        headers['Content-Type'] = 'image/png'
    else:
        raise("File type not accepted")


    response = requests.put(
        url + api_prefix + filename,
        data=data,
        headers=headers,
        timeout=30
    )

    print(response)


def process_img(url, filename, token):

    api_prefix = "imgMetaIndex/indexImage"

    headers = {
        'Authorization': 'Bearer '+token,
        'Content-Type': 'application/json'
    }

    data = {
      "key": f"original/{filename}",
      "metadata": {
        "results": random.randint(0, 1000000),
        "objective": CampaignObjective[random.randint(0, len(CampaignObjective)-1)],
        "node": CampaignNode[random.randint(0, len(CampaignNode)-1)]
      }
    }

    print(data)
    print(url + api_prefix)

    response = requests.post(
        url + api_prefix,
        data=json.dumps(data),
        headers=headers,
        timeout=30
    )

    print(response)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Sample program to call image indexing API')

    #parser.add_argument('--imgs-local-folder', help='Local folder where the images are stored')
    parser.add_argument('--api-url', help='URL of the API to invoke')
    parser.add_argument('--bearer-token', help='Bearer token used for authentication')

    print("before parsing args")

    args = parser.parse_args()

    #imgs_local_folder = args.imgs_local_folder
    api_url = args.api_url
    bearer_token = args.bearer_token

    dataset_location = foz.datasets.find_zoo_dataset("coco-2017", split="validation") # Dataset must have been downloaded

    print(dataset_location)

    #Find all .jpg files in a folder
    img_routes = glob.glob(f"{dataset_location}/data/*.jpg")

    print(img_routes)

    for image_file in img_routes:

        print(image_file)
        filename = image_file.split("/")[-1]
        print(filename)
        put_img(api_url, image_file, filename, bearer_token)

        print("Image uploaded")

        process_img(api_url, filename, bearer_token)

        print("Image processed")

        time.sleep(5)

    print('done')
    exit()