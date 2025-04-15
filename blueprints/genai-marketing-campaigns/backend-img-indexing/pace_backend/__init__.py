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
    Duration,
    CfnOutput,
    aws_iam as iam,
    CfnParameter,
    CustomResource,
)
from constructs import Construct

from pace_backend.index_imgs_workflow import IndexImgWorkflow
from pace_backend.api import IndexImgAPI
from pace_backend.oss_indexing_db import OpenSearchServerlessEmbeddingsIndex

import pace_constructs as pace

from cdk_nag import NagSuppressions, NagPackSuppression


class PACEBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        oss_collection_name = CfnParameter(
            self,
            "OSSCollectionName",
            type="String",
            description="Name for the OpenSearch Serverless collection",
            allowed_pattern="^[a-z\-0-9]*$",
            min_length=3,
            max_length=20,
        )

        oss_embeddings_index_name = CfnParameter(
            self,
            "OSSEmbeddingsIndexName",
            type="String",
            description="Name for the OpenSearch Serverless embeddings index",
            allowed_pattern="^[a-z\-0-9]*$",
            min_length=3,
            max_length=20,
        )

        oss_data_indexing_role_arn = CfnParameter(
            self,
            "OSSDataIndexingRoleARNParam",
            type="String",
            description="The ARN of the IAM role that has access to index data into the OpenSearch Serverless collection",
        )

        oss_data_query_role_arn = CfnParameter(
            self,
            "OSSDataQueryRoleARNParam",
            type="String",
            description="The ARN of the IAM role that has access to query the OpenSearch Serverless collection",
        )

        #Create an IAM role to access the data
        oss_data_indexing_role = iam.Role.from_role_arn(self, "OSSDataIndexingRole",
                                                      oss_data_indexing_role_arn.value_as_string)
        oss_data_query_role = iam.Role.from_role_arn(self, "OSSDataQueryRole",
                                                      oss_data_query_role_arn.value_as_string)

        #Create a bucket to hold the data
        self.imgs_bucket =  pace.PACEBucket(
            self,
            "ImgsBucket"
        )

        #Create OpenSearch Serverless collection
        self.oss_embeddings_index = OpenSearchServerlessEmbeddingsIndex(
            self,
            "OSSEmbeddingsIndex",
            oss_collection_name=oss_collection_name,
            oss_embeddings_index_name=oss_embeddings_index_name,
            oss_data_indexing_role=oss_data_indexing_role,
            oss_data_query_role=oss_data_query_role,
        )

        #Create workflow to index images
        self.img_index_workflow = IndexImgWorkflow(
            self,
            "IdxImgWorkflow",
            imgs_bucket=self.imgs_bucket,
            oss_data_indexing_role=oss_data_indexing_role,
            oss_host=self.oss_embeddings_index.oss_embeddings_collection.attr_collection_endpoint,
            oss_index_name=oss_embeddings_index_name.value_as_string,
        )

        #Create API to index images
        self.img_index_api = IndexImgAPI(
            self,
            "IndexImgAPI",
            imgs_bucket=self.imgs_bucket,
            workflow_machine=self.img_index_workflow.state_machine
        )

        NagSuppressions.add_resource_suppressions_by_path(
            self,
            '/GenAIMarketingCampaigns-ImgIndexStack/LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/ServiceRole/Resource',
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "Managed policy implemented by CDK",
                    "appliesTo": [
                        "Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
                    ],
                },
            ],
            True,
        )

        NagSuppressions.add_resource_suppressions_by_path(
            self,
            '/GenAIMarketingCampaigns-ImgIndexStack/LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/ServiceRole/DefaultPolicy/Resource',
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "Managed policy implemented by CDK",
                },
            ],
            True,
        )

        #Outputs
        CfnOutput(
            self,
            "ImagesBucketName",
            value=self.imgs_bucket.bucket_name,
            export_name=f"{Stack.of(self).stack_name}ImagesBucketName",
        )

        CfnOutput(
            self,
            "EmbeddingsIndexName",
            value=oss_embeddings_index_name.value_as_string,
            export_name=f"{Stack.of(self).stack_name}EmbeddingsIndexName",
        )
