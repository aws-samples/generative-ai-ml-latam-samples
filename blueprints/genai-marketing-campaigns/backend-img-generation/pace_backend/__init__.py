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
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    CfnParameter,
    aws_dynamodb as dynamodb,
    aws_lambda_python_alpha as lambda_python,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_iam as iam,
    aws_apigateway as apigw,
)
from constructs import Construct

import pace_constructs as pace
from pace_backend.api.DownloadImg import DownloadImg

from cdk_nag import NagSuppressions

class PACEBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        oss_collection_host = CfnParameter(
            self,
            "OSSCollectionHostParam",
            type="String",
            description="URL for the OpenSearch Serverless collection",
        )

        oss_embeddings_index_name = CfnParameter(
            self,
            "OSSEmbeddingsIndexNameParam",
            type="String",
            description="Name for the OpenSearch Serverless Embeddings index",
            allowed_pattern="^[a-z\-0-9]*$",
            min_length=3,
            max_length=20,
        )

        oss_collection_arn = CfnParameter(
            self,
            "OSSCollectionARNParam",
            type="String",
            description="ARN for the OpenSearch Serverless collection",
        )

        oss_data_access_role_arn = CfnParameter(
            self,
            "OSSDatAccessRoleARNParam",
            type="String",
            description="The ARN of the IAM role that has access to the OpenSearch Serverless collection",
        )

        imgs_bucket_name = CfnParameter(
            self,
            "S3ImgsBucketParam",
            type="String",
            description="Name of the S3 bucket where the images are stored",
        )

        s3_imgs_bucket = s3.Bucket.from_bucket_name(self, "S3ImgsBucket", imgs_bucket_name.value_as_string)

        oss_data_access_role = iam.Role.from_role_arn(self, "OSSDataAccessRole", oss_data_access_role_arn.value_as_string)
        # Add permissions to IAM role to access the collection
        oss_data_access_role.add_to_principal_policy(
            iam.PolicyStatement(
                actions=["aoss:APIAccessAll"],
                resources=[oss_collection_arn.value_as_string],
                effect=iam.Effect.ALLOW,
            )
        )
        oss_data_access_role.add_to_principal_policy(
            iam.PolicyStatement(
                actions=["aoss:DashboardsAccessAll"],
                resources=[f'arn:aws:aoss:us-east-1:{Stack.of(self).account}:dashboards/default'],
                effect=iam.Effect.ALLOW,
            )
        )
        NagSuppressions.add_resource_suppressions(
            oss_data_access_role,
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Policy implemented by CDK""",
                },
            ],
            True,
        )

        self.api_role = iam.Role(self, "ApiRole", assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"))

        # Default resources
        self.cognito = pace.PACECognito(
            self,
            "ImgGenCognito",
            region=self.region,
        )
        self.apigw = pace.PACEApiGateway(
            self,
            "ImgGenApiGateway",
            region=self.region,
            user_pool=self.cognito.user_pool,
        )

        #S3 proxy integration to download files
        DownloadImg(
            self,
            "DownloadImgMethod",
            api_gw=self.apigw,
            api_role=self.api_role,
            imgs_bucket=s3_imgs_bucket
        )


        # Processed images S3 bucket
        self.processedBucket = pace.PACEBucket(
            self,
            "ProcessedBucket"
        )

        # Raw campaign images S3 bucket
        self.rawImgBucket = pace.PACEBucket(
            self,
            "RawImgBucket"
        )

        #  DynamoDB table
        self.campaignsTable = pace.PACETable(
            self,
            "CampaignsTable",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
        )

        self.historicCampaignsTable = pace.PACETable(
            self,
            "HistoricCampaignsTable",
            partition_key=dynamodb.Attribute(name="img_url", type=dynamodb.AttributeType.STRING),
        )
        self.historicCampaignsTable.add_global_secondary_index(
           partition_key=dynamodb.Attribute(name='nodo', type=dynamodb.AttributeType.STRING), 
           sort_key=dynamodb.Attribute(name='objetivo', type=dynamodb.AttributeType.STRING),
           index_name='search_key')


        self.presign_s3_fn = lambda_python.PythonFunction(
            self,
            "PresignS3",
            entry=os.path.join(os.path.dirname(__file__), "lambda", "presign_s3_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(30),
            memory_size=128,
            environment={
                "LOG_LEVEL": "DEBUG",
                "CAMPAIGN_TABLE_NAME": self.campaignsTable.table_name,
                "HISTORIC_TABLE_NAME": self.historicCampaignsTable.table_name,
                "PROCESSED_BUCKET": self.processedBucket.bucket_name,
                "RAW_IMG_BUCKET": self.rawImgBucket.bucket_name,
            },
            initial_policy=[
                iam.PolicyStatement(
                    actions=[
                        "s3:ListBucket",
                        "s3:GetObject",
                    ],
                    resources=[
                        f'arn:aws:s3:::{self.processedBucket.bucket_name}',
                        f'arn:aws:s3:::{self.processedBucket.bucket_name}/*',
                        f'arn:aws:s3:::{self.rawImgBucket.bucket_name}',
                        f'arn:aws:s3:::{self.rawImgBucket.bucket_name}/*',
                        f'arn:aws:s3:::{s3_imgs_bucket.bucket_name}',
                        f'arn:aws:s3:::{s3_imgs_bucket.bucket_name}/*',
                    ],
                    effect=iam.Effect.ALLOW
                ),
            ],
        )
        #self.processedBucket.grant_read(self.presign_s3_fn.role)
        #self.rawImgBucket.grant_read(self.presign_s3_fn.role)
        NagSuppressions.add_resource_suppressions(
            self.presign_s3_fn.role,
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role created by CDK""",
                },
            ],
            True
        )
        NagSuppressions.add_resource_suppressions(
            self.presign_s3_fn,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role created by CDK""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role created by CDK""",
                },
            ],
            True
        )

        self.get_campaign_fn = lambda_python.PythonFunction(
            self,
            "GetCampaignsFunction",
            entry=os.path.join(os.path.dirname(__file__), "lambda", "get_campaign_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(30),
            memory_size=128,
            environment={
                "LOG_LEVEL": "DEBUG",
                "CAMPAIGN_TABLE_NAME": self.campaignsTable.table_name,
                "HISTORIC_TABLE_NAME": self.historicCampaignsTable.table_name,
                "PROCESSED_BUCKET": self.processedBucket.bucket_name,
                "RAW_IMG_BUCKET": self.rawImgBucket.bucket_name,
            },
        )
        self.campaignsTable.grant_read_data(self.get_campaign_fn.role)
        NagSuppressions.add_resource_suppressions(
            self.get_campaign_fn.role,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role created by CDK""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role created by CDK""",
                },
            ],
            True
        )

        self.delete_campaign_fn = lambda_python.PythonFunction(
            self,
            "DeleteCampaignsFunction",
            entry=os.path.join(os.path.dirname(__file__), "lambda", "delete_campaign_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(120),
            memory_size=128,
            environment={
                "LOG_LEVEL": "DEBUG",
                "CAMPAIGN_TABLE_NAME": self.campaignsTable.table_name,
                "HISTORIC_TABLE_NAME": self.historicCampaignsTable.table_name,
                "PROCESSED_BUCKET": self.processedBucket.bucket_name,
                "RAW_IMG_BUCKET": self.rawImgBucket.bucket_name,
            },
        )
        self.campaignsTable.grant_write_data(self.delete_campaign_fn.role)
        NagSuppressions.add_resource_suppressions(
            self.delete_campaign_fn,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role created by CDK""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role created by CDK""",
                },
            ],
            True
        )

        self.generate_campaign_fn = lambda_python.PythonFunction(
            self,
            "GenerateCampaignConceptFunction",
            entry=os.path.join(os.path.dirname(__file__), "lambda", "generate_campaign_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(90),
            memory_size=128,
            role=oss_data_access_role,
            environment={
                "LOG_LEVEL": "DEBUG",
                "CAMPAIGN_TABLE_NAME": self.campaignsTable.table_name,
                "HISTORIC_TABLE_NAME": self.historicCampaignsTable.table_name,
                "MODEL_ID": "us.amazon.nova-pro-v1:0",
                "REGION": self.region,
            },
        )

        self.generate_campaign_fn.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel"],
                resources=[f"arn:aws:bedrock:*::foundation-model/*",
                           f"arn:aws:bedrock:{Stack.of(self).region}:{Stack.of(self).account}:inference-profile/*"],
            )
        )

        self.campaignsTable.grant_read_data(self.generate_campaign_fn.role)
        self.campaignsTable.grant_write_data(self.generate_campaign_fn.role)
        NagSuppressions.add_resource_suppressions(
            self.generate_campaign_fn,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role created by CDK""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role created by CDK""",
                },
            ],
            True
        )

        self.generate_recommendations_fn = lambda_python.PythonFunction(
            self,
            "GenerateRecommendationsFunction",
            entry=os.path.join(os.path.dirname(__file__), "lambda", "generate_recommendations_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(90),
            memory_size=128,
            role=oss_data_access_role,
            environment={
                "LOG_LEVEL": "DEBUG",
                "CAMPAIGN_TABLE_NAME": self.campaignsTable.table_name,
                "HISTORIC_TABLE_NAME": self.historicCampaignsTable.table_name,
                "OSS_HOST": oss_collection_host.value_as_string,
                "OSS_EMBEDDINGS_INDEX_NAME": oss_embeddings_index_name.value_as_string,
                "REGION": Stack.of(self).region
            },
        )
        self.campaignsTable.grant_read_data(self.generate_recommendations_fn.role)
        self.campaignsTable.grant_write_data(self.generate_recommendations_fn.role)
        self.historicCampaignsTable.grant_read_data(self.generate_recommendations_fn.role)
        self.processedBucket.grant_read(self.generate_recommendations_fn.role)

        s3_imgs_bucket.grant_read(self.generate_recommendations_fn.role)

        self.generate_recommendations_fn.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel"],
                resources=[f"arn:aws:bedrock:{Stack.of(self).region}::foundation-model/*"],
            )
        )

        self.generate_recommendations_fn.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=["*"],
            )
        )
        NagSuppressions.add_resource_suppressions(
            self.generate_recommendations_fn,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role created by CDK""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role created by CDK""",
                },
            ],
            True
        )

        self.generate_prompt_fn = lambda_python.PythonFunction(
            self,
            "GeneratePromptFunction",
            entry=os.path.join(os.path.dirname(__file__), "lambda", "generate_prompt_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(90),
            memory_size=128,
            environment={
                "LOG_LEVEL": "DEBUG",
                "CAMPAIGN_TABLE_NAME": self.campaignsTable.table_name,
                "MODEL_ID": "us.amazon.nova-pro-v1:0"
            },
        )
        self.campaignsTable.grant_read_data(self.generate_prompt_fn.role)
        self.campaignsTable.grant_write_data(self.generate_prompt_fn.role)

        self.generate_prompt_fn.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=["*"],
            )
        )

        self.generate_prompt_fn.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel"],
                resources=[f"arn:aws:bedrock:*::foundation-model/*",
                           f"arn:aws:bedrock:{Stack.of(self).region}:{Stack.of(self).account}:inference-profile/*"],
            )
        )
        NagSuppressions.add_resource_suppressions(
            self.generate_prompt_fn,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role created by CDK""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role created by CDK""",
                },
            ],
            True
        )

        self.update_prompt_fn = lambda_python.PythonFunction(
            self,
            "UpdatePromptFunctionGenerateRecommendationsFunction",
            entry=os.path.join(os.path.dirname(__file__), "lambda", "update_prompt_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(30),
            memory_size=128,
            environment={
                "LOG_LEVEL": "DEBUG",
                "CAMPAIGN_TABLE_NAME": self.campaignsTable.table_name,
                "HISTORIC_TABLE_NAME": self.historicCampaignsTable.table_name,
                "PROCESSED_BUCKET": self.processedBucket.bucket_name,
                "RAW_IMG_BUCKET": self.rawImgBucket.bucket_name,
            },
        )
        self.campaignsTable.grant_read_data(self.update_prompt_fn.role)
        self.campaignsTable.grant_write_data(self.update_prompt_fn.role)
        NagSuppressions.add_resource_suppressions(
            self.update_prompt_fn,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role created by CDK""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role created by CDK""",
                },
            ],
            True
        )

        self.generate_new_images_fn = lambda_python.PythonFunction(
            self,
            "GenerateNewImagesFunction",
            entry=os.path.join(os.path.dirname(__file__), "lambda", "generate_new_images_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(30),
            memory_size=128,
            environment={
                "LOG_LEVEL": "DEBUG",
                "CAMPAIGN_TABLE_NAME": self.campaignsTable.table_name,
                "HISTORIC_TABLE_NAME": self.historicCampaignsTable.table_name,
                "PROCESSED_BUCKET": self.processedBucket.bucket_name,
                "RAW_IMG_BUCKET": self.rawImgBucket.bucket_name,
                "IMG_MODEL_ID": "amazon.nova-canvas-v1:0",
                "REGION": Stack.of(self).region
            },
            initial_policy=[
                iam.PolicyStatement(
                    actions=["bedrock:InvokeModel"],
                    resources=[f"arn:aws:bedrock:{Stack.of(self).region}::foundation-model/*"],
                    effect=iam.Effect.ALLOW
                ),
            ],
        )
        self.campaignsTable.grant_read_data(self.generate_new_images_fn.role)
        self.campaignsTable.grant_write_data(self.generate_new_images_fn.role)
        self.processedBucket.grant_read_write(self.generate_new_images_fn.role)
        NagSuppressions.add_resource_suppressions(
            self.generate_new_images_fn,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role created by CDK""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role created by CDK""",
                },
            ],
            True
        )


        #Add API methods

        #Model for creating campaign
        create_campaign_request_model = self.apigw.rest_api.add_model(
            "CreateCampaignRequest",
            schema=apigw.JsonSchema(
                schema=apigw.JsonSchemaVersion.DRAFT4,
                title="CreateCampaignRequest",
                type=apigw.JsonSchemaType.OBJECT,
                properties={
                    "name": apigw.JsonSchema(type=apigw.JsonSchemaType.STRING),
                    "campaign_description": apigw.JsonSchema(type=apigw.JsonSchemaType.STRING),
                    "objective": apigw.JsonSchema(type=apigw.JsonSchemaType.STRING),
                    "node": apigw.JsonSchema(type=apigw.JsonSchemaType.STRING),
                },
                required=["name", "campaign_description", "objective", "node"],
            ),
            content_type="application/json",
        )

        #Model for creating prompt
        create_prompt_request_model = self.apigw.rest_api.add_model(
            "GeneratePromptRequest",
            schema=apigw.JsonSchema(
                schema=apigw.JsonSchemaVersion.DRAFT4,
                title="GeneratePromptRequest",
                type=apigw.JsonSchemaType.OBJECT,
                properties={
                    "references": apigw.JsonSchema(
                        type=apigw.JsonSchemaType.ARRAY,
                        items=apigw.JsonSchema(type=apigw.JsonSchemaType.STRING)
                    ),
                },
                required=["references"],
            ),
            content_type="application/json",
        )

        self.apigw.add_method(
            resource_path="/presign",
            http_method="POST",
            lambda_function=self.presign_s3_fn,
            request_validator=self.apigw.request_body_validator,
        )

        self.apigw.add_method(
            resource_path="/campaigns",
            http_method="GET",
            lambda_function=self.get_campaign_fn,
            request_validator=self.apigw.request_body_validator,
        )

        self.apigw.add_method(
            resource_path="/campaigns/{id}",
            http_method="GET",
            lambda_function=self.get_campaign_fn,
            request_validator=self.apigw.request_body_validator,
        )

        self.apigw.add_method(
            resource_path="/campaigns/{id}",
            http_method="DELETE",
            lambda_function=self.delete_campaign_fn,
            request_validator=self.apigw.request_body_validator,
        )

        self.apigw.add_method(
            resource_path="/campaigns",
            http_method="POST",
            lambda_function=self.generate_campaign_fn,
            request_validator=self.apigw.request_body_validator,
            request_models={
                "application/json": create_campaign_request_model
            }
        )

        self.apigw.add_method_async(
            resource_path="/references/{id}",
            http_method="POST",
            lambda_function=self.generate_recommendations_fn,
            request_validator=self.apigw.request_body_validator,
        )

        self.apigw.add_method_async2(
            resource_path="/suggestion/{id}",
            http_method="POST",
            lambda_function=self.generate_prompt_fn,
            request_validator=self.apigw.request_body_validator,
            request_models={
                "application/json": create_prompt_request_model
            }
        )

        self.apigw.add_method(
            resource_path="/suggestion/{id}",
            http_method="PUT",
            lambda_function=self.update_prompt_fn,
            request_validator=self.apigw.request_body_validator,
        )

        self.apigw.add_method(
            resource_path="/generate_images/{id}",
            http_method="POST",
            lambda_function=self.generate_new_images_fn,
            request_validator=self.apigw.request_body_validator,
        )

        CfnOutput(
            self,
            "RegionName",
            value=self.region,
            export_name=f"{Stack.of(self).stack_name}RegionName",
        )
