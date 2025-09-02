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
import aws_cdk
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    CfnParameter,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    aws_sns_subscriptions as sns_subs,
    aws_dynamodb as dynamodb,
    aws_lambda_python_alpha as lambda_python,
    aws_lambda as lambda_,
    aws_kms as kms,
    aws_s3 as s3,
    aws_logs as logs,
    aws_s3_notifications as s3n,
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_sns_subscriptions as sns_subscriptions,
    aws_pipes_alpha as pipes,
    aws_pipes_sources_alpha as pipes_sources,
    aws_pipes_targets_alpha as pipes_targets,
)

from constructs import Construct

import pace_constructs as pace

from cdk_nag import NagSuppressions

APP_DIR = os.path.join(os.path.dirname(__file__), "../../..", "app")

class DocumentIndexingStack(Construct):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            pages_per_chunk: str,
            questions_per_chunk: str,
            language_code: str,
            #metadata_table: dynamodb.Table,
            oss_data_indexing_role: iam.Role,
            oss_host: str,
            oss_index_name: str,
            shared_utils_layer: lambda_python.PythonLayerVersion,
            **kwargs
    ) -> None:

        super().__init__(scope, construct_id, **kwargs)

        # KMS keys for this app
        self.sqs_kms_key = kms.Key(self,
                                   "DocIndexing-SQS-KMSKey",
                                   alias=f"sqs-key-{Stack.of(self).stack_name}",
                                   enable_key_rotation=True
                                   )

        # A S3 bucket to store the documents
        self.docs_bucket = pace.PACEBucket(
            self,
            "DocumentsBucket"
        )

        # A DynamoDB table to store the results of the processed documents
        self.jobs_table = pace.PACETable(
            self,
            "StatusTable",
            partition_key=dynamodb.Attribute(name="document_key", type=dynamodb.AttributeType.STRING),
        )

        self.summaries_table = pace.PACETable(
            self,
            "Meta-Knowledge-SummariesTable",
            partition_key=dynamodb.Attribute(name="summary_key", type=dynamodb.AttributeType.STRING),
        )

        # Create a log group for the workflow
        workflow_log_group = logs.LogGroup(
            self,
            "DocIndexingWorkflowLogGroup",
            retention=logs.RetentionDays.ONE_MONTH,
            log_group_name='MetaKBIndexingWorkflowLogs',
            removal_policy=aws_cdk.RemovalPolicy.DESTROY
        )

        # An Amazon SNS topic
        self.sns_topic = sns.Topic(
            self,
            "SNSTextractTopic",
            display_name="AmazonTextract-AsyncJobsTopic",
            topic_name="AmazonTextract-AsyncJobsTopic"
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

        ########################------------------LAMBDA FUNCTIONS-------------------#######################

        # Lambda function to chunk document
        self.chunk_document_lambda = lambda_python.PythonFunction(
            self,
            "ChunkDocumentLambda",
            entry=os.path.join(APP_DIR, "lambda/document_indexing_workflow/chunk_textract_document_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "chunk_document_lambda",
                "PAGE_CHUNK_SIZE": pages_per_chunk,
                "JOBS_DYNAMO_DB_TABLE_NAME": self.jobs_table.table_name,
                "DOCUMENT_BUCKET_NAME": self.docs_bucket.bucket_name
            },
            timeout=Duration.minutes(5),
            memory_size=512
        )

        self.chunk_document_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "textract:GetDocumentTextDetection"
                ],
                resources=["*"],
            )
        )
        self.jobs_table.grant_read_write_data(self.chunk_document_lambda)
        self.docs_bucket.grant_read_write(self.chunk_document_lambda)

        NagSuppressions.add_resource_suppressions(
            self.chunk_document_lambda,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda document chunking. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda document chunking. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        # Lambda function to extract metadata from chunk
        self.extract_metadata_from_chunk_lambda = lambda_python.PythonFunction(
            self,
            "ExtractMetadataFromChunkLambda",
            entry=os.path.join(APP_DIR, "lambda/document_indexing_workflow/generate_chunk_metadata_llm_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "metadata_extraction_lambda",
                "REGION": Stack.of(self).region,
                "BEDROCK_REGION": Stack.of(self).region,
                "BEDROCK_MODEL_ID": "us.amazon.nova-lite-v1:0", #Inference profile instead of model Id
                "LANGUAGE_ID": language_code,
                "JOBS_DYNAMO_DB_TABLE_NAME": self.jobs_table.table_name,
                "DOCUMENT_BUCKET_NAME": self.docs_bucket.bucket_name
            },
            timeout=Duration.minutes(15),  # MAX VALUE, DO NOT INCREASE
            memory_size=512
        )

        self.extract_metadata_from_chunk_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel"
                ],
                resources=["*"],
            )
        )

        self.jobs_table.grant_read_write_data(self.extract_metadata_from_chunk_lambda)
        self.docs_bucket.grant_read(self.extract_metadata_from_chunk_lambda)

        NagSuppressions.add_resource_suppressions(
            self.extract_metadata_from_chunk_lambda,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda document metadata extraction. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda document metadata extraction. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        # Lambda function to generate metadata for document
        self.generate_doc_metadata_lambda = lambda_python.PythonFunction(
            self,
            "GenerateDocumentMetadataLambda",
            entry=os.path.join(APP_DIR, "lambda/document_indexing_workflow/generate_doc_metadata_llm_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "doc_metadata_gen_lambda",
                "REGION": Stack.of(self).region,
                "BEDROCK_REGION": Stack.of(self).region,
                "BEDROCK_MODEL_ID": "us.amazon.nova-pro-v1:0",  # Inference profile instead of model Id
                "LANGUAGE_ID": language_code,
                "JOBS_DYNAMO_DB_TABLE_NAME": self.jobs_table.table_name
            },
            timeout=Duration.minutes(15),  # MAX VALUE, DO NOT INCREASE
            memory_size=1024
        )

        self.generate_doc_metadata_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel"
                ],
                resources=["*"],
            )
        )

        self.jobs_table.grant_read_write_data(self.generate_doc_metadata_lambda)

        NagSuppressions.add_resource_suppressions(
            self.generate_doc_metadata_lambda,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda document metadata generation. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda document metadata generation. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        # Lambda function to create Q&A from chunk
        self.generate_qa_from_chunk_lambda = lambda_python.PythonFunction(
            self,
            "GenerateQAFromChunkLambda",
            entry=os.path.join(APP_DIR, "lambda/document_indexing_workflow/generate_chunk_qa_llm_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "qa_gen_lambda",
                "REGION": Stack.of(self).region,
                "BEDROCK_REGION": Stack.of(self).region,
                "BEDROCK_MODEL_ID": "us.anthropic.claude-3-5-haiku-20241022-v1:0", #Inference profile instead of model Id
                "STRUCTURED_MODEL_ID": "us.amazon.nova-pro-v1:0",
                "LANGUAGE_ID": language_code,
                "MAX_N_QUESTIONS": questions_per_chunk,
                "JOBS_DYNAMO_DB_TABLE_NAME": self.jobs_table.table_name,
                "DOCUMENT_BUCKET_NAME": self.docs_bucket.bucket_name
            },
            timeout=Duration.minutes(15),  # MAX VALUE, DO NOT INCREASE
            memory_size=1024
        )

        self.generate_qa_from_chunk_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel"
                ],
                resources=["*"],
            )
        )

        self.jobs_table.grant_read_write_data(self.generate_qa_from_chunk_lambda)
        self.docs_bucket.grant_read_write(self.generate_qa_from_chunk_lambda)

        NagSuppressions.add_resource_suppressions(
            self.generate_qa_from_chunk_lambda,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda document QA extraction. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda document QA extraction. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        # Lambda function to create document Q&A
        self.generate_document_qa_lambda = lambda_python.PythonFunction(
            self,
            "GenerateDocumentQALambda",
            entry=os.path.join(APP_DIR, "lambda/document_indexing_workflow/generate_doc_qa_llm_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "doc_qa_gen_lambda",
                "REGION": Stack.of(self).region,
                "BEDROCK_REGION": Stack.of(self).region,
                "BEDROCK_MODEL_ID": "us.anthropic.claude-3-5-haiku-20241022-v1:0", #Inference profile instead of model Id
                "STRUCTURED_MODEL_ID": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",  # Inference profile instead of model Id
                "LANGUAGE_ID": language_code,
                "MAX_N_QUESTIONS": questions_per_chunk,
                "JOBS_DYNAMO_DB_TABLE_NAME": self.jobs_table.table_name,
                "DOCUMENT_BUCKET_NAME": self.docs_bucket.bucket_name
            },
            timeout=Duration.minutes(15),  # MAX VALUE, DO NOT INCREASE
            memory_size=1024
        )

        self.generate_document_qa_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel"
                ],
                resources=["*"],
            )
        )

        self.jobs_table.grant_read_write_data(self.generate_document_qa_lambda)
        self.docs_bucket.grant_read_write(self.generate_document_qa_lambda)

        NagSuppressions.add_resource_suppressions(
            self.generate_document_qa_lambda,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda document QA extraction. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda document QA extraction. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        # Lambda function to create Meta-knowledge base summaries from chunk
        self.generate_meta_kb_summary_lambda = lambda_python.PythonFunction(
            self,
            "GenerateMetaKBLambda",
            entry=os.path.join(APP_DIR, "lambda/document_indexing_workflow/generate_meta_kb_summary_llm_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "summary_gen_lambda",
                "REGION": Stack.of(self).region,
                "BEDROCK_REGION": Stack.of(self).region,
                "BEDROCK_MODEL_ID": "us.amazon.nova-lite-v1:0",  # Inference profile instead of model Id
                "LANGUAGE_ID": language_code,
                "JOBS_DYNAMO_DB_TABLE_NAME": self.jobs_table.table_name,
                "DOCUMENTS_DYNAMO_DB_TABLE_NAME": self.summaries_table.table_name,
                "DOCUMENT_BUCKET_NAME": self.docs_bucket.bucket_name
            },
            timeout=Duration.minutes(15),  # MAX VALUE, DO NOT INCREASE
            memory_size=1024
        )

        self.generate_meta_kb_summary_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel"
                ],
                resources=["*"],
            )
        )

        self.summaries_table.grant_read_write_data(self.generate_meta_kb_summary_lambda)
        self.jobs_table.grant_read_write_data(self.generate_meta_kb_summary_lambda)
        self.docs_bucket.grant_read(self.generate_meta_kb_summary_lambda)

        NagSuppressions.add_resource_suppressions(
            self.generate_meta_kb_summary_lambda,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda meta-kb summary extraction. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda meta-kb summary QA extraction. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        # Lambda function to index data to open search serverless
        self.index_to_meta_kb_lambda = lambda_python.PythonFunction(
            self,
            "IndexDocToMetaKBLambda",
            entry=os.path.join(APP_DIR, "lambda/document_indexing_workflow/index_data_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "index_doc_lambda",
                "REGION": Stack.of(self).region,
                "BEDROCK_REGION": Stack.of(self).region,
                "BEDROCK_MODEL_ID": "amazon.titan-embed-text-v2:0",
                "LANGUAGE_ID": language_code,
                "JOBS_DYNAMO_DB_TABLE_NAME": self.jobs_table.table_name,
                "OSS_HOST": oss_host,
                "OSS_EMBEDDINGS_INDEX_NAME": oss_index_name,
                "DOCUMENTS_DYNAMO_DB_TABLE_NAME": self.summaries_table.table_name,
                "DOCUMENT_BUCKET_NAME": self.docs_bucket.bucket_name
            },
            role=oss_data_indexing_role,
            timeout=Duration.minutes(15),  # MAX VALUE, DO NOT INCREASE
        )

        oss_data_indexing_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel"
                ],
                resources=["*"],
            )
        )

        self.jobs_table.grant_read_write_data(self.index_to_meta_kb_lambda)
        self.docs_bucket.grant_read(self.index_to_meta_kb_lambda)

        NagSuppressions.add_resource_suppressions(
            oss_data_indexing_role,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda meta-kb indexing. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda meta-kb indexing. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        ########################------------------LAMBDA FUNCTIONS-------------------#######################

        #######################------------------STEP FUNCTIONS WORKFLOW-------------#######################

        # Create step functions tasks

        # Task to chunk documents
        chunk_document_task = sfn_tasks.LambdaInvoke(
            self,
            'ChunkDocumentTask',
            lambda_function=self.chunk_document_lambda,
            result_selector={
                "statusCode.$": "$.Payload.statusCode",
                "job_id.$": "$.Payload.job_id",
                "document_key.$": "$.Payload.document_key",
                "document_name.$": "$.Payload.document_name",
                "requestId.$": "$.SdkResponseMetadata.RequestId",
                "n_chunks.$": "$.Payload.n_chunks",
                "pages_chunk_size.$": "$.Payload.pages_chunk_size",
                "chunk_keys.$": "$.Payload.chunk_keys"
            }
        )

        # Task to generate metadata for chunk
        generate_chunk_metadata_task = sfn_tasks.LambdaInvoke(
            self,
            'GenerateChunkMetadata',
            lambda_function=self.extract_metadata_from_chunk_lambda,
            result_selector={
                "metadata.$": "$.Payload.body.doc_metadata",
                #"document_name.$": "$.Payload.body.document_name",
                #"document_key.$": "$.Payload.body.document_key",
                #"chunk_index.$": "$.Payload.body.chunk_index",
                "statusCode.$": "$.Payload.statusCode",
                "requestId.$": "$.SdkResponseMetadata.RequestId"
            },
            result_path="$.MetadataTask"
        )

        # Task to generate metadata for document
        generate_doc_metadata_task = sfn_tasks.LambdaInvoke(
            self,
            'GenerateDocMetadata',
            lambda_function=self.generate_doc_metadata_lambda,
            result_selector={
                "metadata.$": "$.Payload.body.doc_metadata",
                "document_name.$": "$.Payload.body.document_name",
                "document_key.$": "$.Payload.body.document_key",
                "statusCode.$": "$.Payload.statusCode",
                "requestId.$": "$.SdkResponseMetadata.RequestId"
            },
        )

        # Task to generate QA for chunk
        generate_chunk_qa_task = sfn_tasks.LambdaInvoke(
            self,
            'GenerateChunkQATask',
            lambda_function=self.generate_qa_from_chunk_lambda,
            result_selector={
                "statusCode.$": "$.Payload.statusCode",
                "chunk_index.$": "$.Payload.chunk_index",
                "document_key.$": "$.Payload.document_key",
                "document_name.$": "$.Payload.document_name",
                "requestId.$": "$.SdkResponseMetadata.RequestId"
            }
        )

        # Task to generate QA for document
        generate_doc_qa_task = sfn_tasks.LambdaInvoke(
            self,
            'GenerateDocQATask',
            lambda_function=self.generate_document_qa_lambda,
            result_selector={
                "statusCode.$": "$.Payload.statusCode",
                "document_name.$": "$.Payload.document_name",
                "document_key.$": "$.Payload.document_key",
                "requestId.$": "$.SdkResponseMetadata.RequestId"
            },
        )

        # Task to generate meta-knowledge summary
        generate_mk_summary_task = sfn_tasks.LambdaInvoke(
            self,
            'GenerateMKSummaryTask',
            lambda_function=self.generate_meta_kb_summary_lambda,
            payload=sfn.TaskInput.from_object({
                "document_name": sfn.JsonPath.string_at("$[0].document_name"),
                "document_key": sfn.JsonPath.string_at("$[0].document_key"),
                "metadata": sfn.JsonPath.string_at("$[0].metadata"),
            }),
            result_selector={
                "metadata.$": "$.Payload.body.metadata",
                "document_key.$": "$.Payload.body.document_key",
                "document_name.$": "$.Payload.body.document_name",
                "statusCode.$": "$.Payload.statusCode",
                "requestId.$": "$.SdkResponseMetadata.RequestId"
            }
        )

        # Task toindex meta-knowledge base
        index_meta_kb_task = sfn_tasks.LambdaInvoke(
            self,
            'IndexMetaKBTask',
            lambda_function=self.index_to_meta_kb_lambda,
        )

        sfn_parallel_doc_process = sfn.Parallel(self, "ParallelDocumentProcessing")

        sfn_metadata_map = sfn.Map(self,
                          'ChunkIteratorMetadataMap',
                          items_path='$.chunk_keys',
                          item_selector={
                              'chunk_index.$': '$$.Map.Item.Index',
                              'chunk_s3_key.$': '$$.Map.Item.Value',
                              'document_key.$': '$.document_key',
                              'document_name.$': '$.document_name'
                          },
                          max_concurrency=5,
                          )

        sfn_qa_map = sfn.Map(self,
                          'ChunkIteratorQAMap',
                          items_path='$.chunk_keys',
                          item_selector={
                              'chunk_index.$': '$$.Map.Item.Index',
                              'chunk_s3_key.$': '$$.Map.Item.Value',
                              'document_key.$': '$.document_key',
                              'document_name.$': '$.document_name'
                          },
                          max_concurrency=5,
                          )

        sfn_metadata_map.item_processor(generate_chunk_metadata_task)
        sfn_qa_map.item_processor(generate_chunk_qa_task)

        sfn_parallel_doc_process.branch(sfn_metadata_map.next(generate_doc_metadata_task))
        sfn_parallel_doc_process.branch(sfn_qa_map.next(generate_doc_qa_task))
        sfn_parallel_doc_process.next(generate_mk_summary_task).next(index_meta_kb_task)

        # Create step functions state machine

        #chunk_document_task.next(sfn_map).next(consolidate_mk_base_task)
        chunk_document_task.next(sfn_parallel_doc_process)
        definition = chunk_document_task

        self.meta_kb_indexing_pipeline_sfn = sfn.StateMachine(
            self,
            'MetaKBIndexingWorkflow',
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            logs=sfn.LogOptions(
                level=sfn.LogLevel.ALL,
                destination=workflow_log_group
            ),
            tracing_enabled=True
        )

        NagSuppressions.add_resource_suppressions(
            self.meta_kb_indexing_pipeline_sfn,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for meta knowledge base workflow. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for meta knowledge base workflow. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        #######################------------------STEP FUNCTIONS WORKFLOW-------------#######################

        # Create Event Bridge pipes to initiate state machine on SQS message

        sfn_pipe_target = pipes_targets.SfnStateMachine(
            self.meta_kb_indexing_pipeline_sfn,
            invocation_type=pipes_targets.StateMachineInvocationType.FIRE_AND_FORGET
        )

        self.event_bridge_pipe = pipes.Pipe(
            self,
            "SQS-SFN-DocIndexingPipe",
            source=pipes_sources.SqsSource(self.sqs_queue),
            target=sfn_pipe_target
        )