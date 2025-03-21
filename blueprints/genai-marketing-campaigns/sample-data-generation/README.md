# GenAI Marketing Campaigns - Sample images indexing

The scripts in this folder will help you index sample images to test the application

## Pre-requisites

To successfully deploy and run this stack you must:

* Configure the AWS Credentials in your environment. Refer to [Configuration and credential file settings](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html).
* Python >= 3.10
* Have deployed the **Previous Campaigns Indexing** stack

## Setup

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
.venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
pip install -r requirements.txt
```

## Sample dataset

The sample dataset is the [COCO](https://cocodataset.org/#home) dataset which is a large-scale object detection, segmentation, and captioning dataset. Although this dataset is meant for training ML models for task such as object detection and image segmentation (it is labeled dataset) we will only use the images of the dataset and disregard the labels.

**NOTE:** We do not distribute the dataset, rather you will be instructed to download a sample of the dataset and index it yourself.

### Download a sample of the COCO dataset

To download a sample of the dataset you can use the *coco_data_sample.py* script. It will download N samples (images) of the COCO dataset under the following categories:

* snowboard 
* sports ball
* baseball bat
* baseball glove
* skateboard
* surfboard
* tennis racket

The following command will download N samples to your local computer:

```
python coco_data_sample.py --num-images N
```

where **N** is the number of images you would like to download. By default, the dataset will be downloaded to a specific location under *$HOME/fiftyone/coco-2017*


## Index the sample images

To index the sample images simply run

```
python index_images.py \
--api-url <<ImgIndexStack.IndexImgAPIApiGatewayRestApiEndpoint>> \
--bearer-token <<ImgIndexStack Cognito Bearer Token>>
```

Notice you can modify this script to index your own images instead of the sample images.

