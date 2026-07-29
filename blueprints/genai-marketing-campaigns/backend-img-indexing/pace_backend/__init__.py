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

from aws_cdk import (
    Stack,
    CfnOutput,
)
from constructs import Construct

from pace_backend.index_imgs_workflow import IndexImgWorkflow
from pace_backend.api import IndexImgAPI
from pace_backend.s3_vectors_db import S3VectorsEmbeddingsIndex

import pace_constructs as pace


class PACEBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #Create a bucket to hold the data
        self.imgs_bucket =  pace.PACEBucket(
            self,
            "ImgsBucket"
        )

        #Create the S3 Vectors bucket and embeddings index
        self.embeddings_index = S3VectorsEmbeddingsIndex(
            self,
            "EmbeddingsIndex",
        )

        #Create workflow to index images
        self.img_index_workflow = IndexImgWorkflow(
            self,
            "IdxImgWorkflow",
            imgs_bucket=self.imgs_bucket,
            vector_bucket_name=self.embeddings_index.vector_bucket_name,
            vector_index_name=self.embeddings_index.vector_index_name,
            vector_index_arn=self.embeddings_index.vector_index_arn,
        )

        #Create API to index images
        self.img_index_api = IndexImgAPI(
            self,
            "IndexImgAPI",
            imgs_bucket=self.imgs_bucket,
            workflow_machine=self.img_index_workflow.state_machine
        )

        #Outputs
        CfnOutput(
            self,
            "ImagesBucketName",
            value=self.imgs_bucket.bucket_name,
            export_name=f"{Stack.of(self).stack_name}ImagesBucketName",
        )
