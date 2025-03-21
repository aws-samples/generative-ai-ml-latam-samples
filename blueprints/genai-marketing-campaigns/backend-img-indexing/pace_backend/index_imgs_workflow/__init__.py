# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os

from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_lambda_python_alpha as lambda_python,
    aws_logs as logs,
    aws_s3 as s3,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    Duration,
)
from constructs import Construct

from cdk_nag import NagSuppressions


class IndexImgWorkflow(Construct):
    """A Step Functions express workflow that takes an image file and indexes the image into Amazon OpenSearch"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        imgs_bucket: s3.IBucket,
        oss_data_indexing_role: iam.Role,
        oss_host: str,
        oss_index_name: str,
    ) -> None:
        super().__init__(scope, construct_id)

        # Create a log group for the workflow
        workflow_log_group = logs.LogGroup(
            self,
            "WorkflowLogGroup",
            retention=logs.RetentionDays.ONE_MONTH,
        )

        # A lambda function to extract the elements of the image
        describe_img_fn = lambda_python.PythonFunction(
            self,
            "DescribeImgFunction",
            entry=f"{os.path.dirname(os.path.realpath(__file__))}/describe_image_fn",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(30),
            memory_size=128,
            environment={
                "LOG_LEVEL": "DEBUG",
                "IMG_BUCKET": imgs_bucket.bucket_name,
                "MODEL_ID": "us.amazon.nova-pro-v1:0"
            },
        )

        describe_img_fn.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel"],
                resources=[f"arn:aws:bedrock:*::foundation-model/*",
                           f"arn:aws:bedrock:{Stack.of(self).region}:{Stack.of(self).account}:inference-profile/*"],
            )
        )

        imgs_bucket.grant_read(describe_img_fn)

        NagSuppressions.add_resource_suppressions(
            describe_img_fn,
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

        # A lambda function to get the image embeddings
        embed_img_fn = lambda_python.PythonFunction(
            self,
            "EmbedImgFunction",
            entry=f"{os.path.dirname(os.path.realpath(__file__))}/get_img_embeddings_fn",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(60),
            memory_size=128,
            environment={
                "LOG_LEVEL": "DEBUG",
                "IMG_BUCKET": imgs_bucket.bucket_name
            },
        )

        embed_img_fn.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel"],
                resources=[f"arn:aws:bedrock:{Stack.of(self).region}::foundation-model/*"],
            )
        )

        imgs_bucket.grant_read(embed_img_fn)

        NagSuppressions.add_resource_suppressions(
            embed_img_fn,
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

        # A lambda function index the image embeddings and metadata
        index_data_fn = lambda_python.PythonFunction(
            self,
            "IndexDataFunction",
            entry=f"{os.path.dirname(os.path.realpath(__file__))}/index_data_fn",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(10),
            environment={
                "LOG_LEVEL": "INFO",
                "IMG_BUCKET": imgs_bucket.bucket_name,
                "OSS_HOST": oss_host,
                "OSS_EMBEDDINGS_INDEX_NAME": oss_index_name
            },
            role=oss_data_indexing_role,
        )

        NagSuppressions.add_resource_suppressions(
            index_data_fn,
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

        #Lambda step functions workflow definition

        describe_image_task = tasks.LambdaInvoke(
            self,
            "DescribeImageTask",
            lambda_function=describe_img_fn,
            result_selector={
              "labels_list.$": "$.Payload.body.labels_list",
              "description.$": "$.Payload.body.description"
            },
            result_path="$.img_desc",
        )

        embed_img_task = tasks.LambdaInvoke(
            self,
            "EmbedImgTask",
            lambda_function=embed_img_fn,
            payload=sfn.TaskInput.from_object({
              "img_key.$":"$.img_key"
            }),
            result_selector={
              "embedding.$": "$.Payload.body.embedding.embedding"
            },
            result_path="$.embedding",
        )

        index_img_task = tasks.LambdaInvoke(
            self,
            "IndexImgTask",
            lambda_function=index_data_fn,
            payload=sfn.TaskInput.from_object({
              "metadata.$":"$.metadata",
              "img_key.$":"$.img_key",
              "img_desc.$": "$.img_desc.description",
              "labels_list.$":"$.img_desc.labels_list",
              "embeddings.$":"$.embedding.embedding"
            }),
        )

        describe_image_task.next(embed_img_task)
        embed_img_task.next(index_img_task)

        # state machine
        self.state_machine = sfn.StateMachine(
            self,
            "StateMachine",
            definition_body=sfn.DefinitionBody.from_chainable(describe_image_task),
            logs=sfn.LogOptions(
                destination=workflow_log_group,
                level=sfn.LogLevel.ALL,
                include_execution_data=True,
            ),
            tracing_enabled=True,
            state_machine_type=sfn.StateMachineType.EXPRESS,
        )

        NagSuppressions.add_resource_suppressions(
            self.state_machine,
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




