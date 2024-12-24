# MIT No Attribution
#
# Copyright 2024 Amazon Web Services
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
from email.policy import default

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    CfnParameter,
    aws_dynamodb as dynamodb,
    aws_sns_subscriptions as sns_subs,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_iam as iam,
    aws_kms as kms,
    aws_lambda_python_alpha as lambda_python,
    aws_lambda as lambda_,
    aws_pipes_alpha as pipes,
    aws_pipes_sources_alpha as pipes_sources,
    aws_pipes_targets_alpha as pipes_targets,
)
from constructs import Construct
from cdk_nag import NagSuppressions, NagPackSuppression

import pace_constructs as pace

from .api import DocumentAPI
from .text_analysis_workflow import DocAnalysisSFNPipeline


class PACEBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        language_code = CfnParameter(
            self,
            "LanguageCode",
            type="String",
            description="Language of the documents to be processed",
            allowed_values=["en", "es"],
            default="es"
        )

        include_examples = CfnParameter(
            self,
            "IncludeExamples",
            type="String",
            description="Wether to include or not examples for the data extraction",
            allowed_values=["true", "false"],
            default="false"
        )

        pages_chunk = CfnParameter(
            self,
            "PagesChunk",
            type="String",
            description="The number of pages per chunk",
            allowed_pattern="\d",
            default="5"
        )

        extraction_confidence_level = CfnParameter(
            self,
            "ExtractionConfidenceLevel",
            type="String",
            description="Threshold for filtering extractions based on the model's certainty",
            allowed_pattern="\d\d",
            default="85"
        )

        # KMS keys for this app
        self.sns_kms_key = kms.Key(self,
                                   "SNS-KMSKey",
                                   alias=f"sns-key-{Stack.of(self).stack_name}",
                                   enable_key_rotation=True
                                   )
        self.sqs_kms_key = kms.Key(self,
                                   "SQS-KMSKey",
                                   alias=f"sqs-key-{Stack.of(self).stack_name}",
                                   enable_key_rotation=True
                                   )

        # A S3 bucket to store the documents
        self.docs_bucket = pace.PACEBucket(
            self,
            "Documents-Bucket"
        )

        # A S3 bucket to store the reports
        self.reports_bucket = pace.PACEBucket(
            self,
            "Reports-Bucket"
        )

        # A DynamoDB table to store the results of the processed documents
        self.documents_table = pace.PACETable(
            self,
            "DocumentsTable",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
        )

        # An Amazon SNS topic
        self.sns_topic = sns.Topic(
            self,
            "SNSTextractTopic",
            display_name="AmazonTextract-AsyncJobsTopic",
            topic_name="AmazonTextract-AsyncJobsTopic",
            #master_key=self.sns_kms_key,
        )

        self.sns_topic.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["sns:Publish"],
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                resources=[self.sns_topic.topic_arn],
                conditions={
                    "Bool": {"aws:SecureTransport": "false"},
                }
            )
        )

        self.sns_topic.add_to_resource_policy(
            iam.PolicyStatement(
                actions=[
                    "SNS:Publish",
                    "SNS:RemovePermission",
                    "SNS:SetTopicAttributes",
                    "SNS:DeleteTopic",
                    "SNS:ListSubscriptionsByTopic",
                    "SNS:GetTopicAttributes",
                    "SNS:AddPermission",
                    "SNS:Subscribe"
                ],
                effect=iam.Effect.ALLOW,
                principals=[iam.AnyPrincipal()],
                resources=[self.sns_topic.topic_arn],
                conditions={
                    "StringEquals": {"aws:SourceOwner": Stack.of(self).account},
                }
            )
        )

        NagSuppressions.add_resource_suppressions(
            self.sns_topic,
            [
                {
                    "id": "AwsSolutions-SNS2",
                    "reason": """Textract doesnt support SNS topics with encryption enabled""",
                },
            ],
            True
        )

        # An SQS Queue to subscribe to the SNS topic
        self.sqs_queue = sqs.Queue(
            self,
            "SQSTextractQueue",
            visibility_timeout=Duration.seconds(60 * 5),
            queue_name="AmazonTextract-AsyncJobsQueue",
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=self.sqs_kms_key,
            enforce_ssl=True
        )

        # A dead letter SQS queue for the main SQS queue
        self.sqs_dead_letter_queue = sqs.Queue(
            self,
            "SQSTextractDeadLetterQueue",
            visibility_timeout=Duration.seconds(60 * 5),
            queue_name="AmazonTextract-AsyncJobsDeadLetterQueue",
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=self.sqs_kms_key,
            enforce_ssl=True,
            retention_period=Duration.days(14),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=self.sqs_queue,
            ),
        )

        self.sns_topic.add_subscription(sns_subs.SqsSubscription(self.sqs_queue))

        # An IAM role to send messages from Amazon Textract to an SNS Topic
        self.textract_sns_role = iam.Role(
            self,
            "SNSTextractRole",
            assumed_by=iam.ServicePrincipal("textract.amazonaws.com"),
            description="Role to send messages from Amazon Textract to an SNS Topic",
            inline_policies={
                "SendMessagesToSNSTopic": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["sns:Publish"],
                            resources=[self.sns_topic.topic_arn],
                        )
                    ]
                )
            },
        )

        self.sns_topic.grant_publish(self.textract_sns_role)

        # Shared Lambda layer with Python packaging for steps status
        self.shared_status_lambda_layer = lambda_python.PythonLayerVersion(
            self,
            "StatusEnumLayer",
            entry=os.path.join(os.path.dirname(__file__), "shared"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_13],
        )

        # Create API from construct
        self.api = DocumentAPI(
            self,
            "Documents-Api",
            document_bucket=self.docs_bucket,
            report_bucket=self.reports_bucket,
            documents_table=self.documents_table,
            sns_textract_topic=self.sns_topic,
            sns_textract_role=self.textract_sns_role,
            shared_status_lambda_layer=self.shared_status_lambda_layer
        )

        # Create step functions document analysis workflow
        self.sfn_doc_analysis = DocAnalysisSFNPipeline(
            self,
            "DocAnalysisSFNPipeline",
            dynamo_docs_table=self.documents_table,
            output_s3_bucket=self.reports_bucket,
            shared_status_lambda_layer=self.shared_status_lambda_layer,
            language_code=language_code.value_as_string,
            pages_chunk=pages_chunk.value_as_string,
            use_examples=True if include_examples.value_as_string == "true" else False,
            extraction_confidence_level=extraction_confidence_level.value_as_string
        )

        # Create Event Bridge pipes to initiate state machine on SQS message

        sfn_pipe_target = pipes_targets.SfnStateMachine(
            self.sfn_doc_analysis.document_processing_pipeline_sfn,
            invocation_type=pipes_targets.StateMachineInvocationType.FIRE_AND_FORGET
        )

        self.event_bridge_pipe = pipes.Pipe(
            self,
            "SQS-SFN-DocAnalysisPipe",
            source=pipes_sources.SqsSource(self.sqs_queue),
            target=sfn_pipe_target
        )

        CfnOutput(
            self,
            "RegionName",
            value=self.region,
            export_name=f"{Stack.of(self).stack_name}RegionName",
        )

        # cdk-nag suppressions
        stack_suppressions = [
            # Insert your stack-level NagPackSuppression"s here
        ]
        NagSuppressions.add_stack_suppressions(
            stack=self,
            suppressions=stack_suppressions,
        )
