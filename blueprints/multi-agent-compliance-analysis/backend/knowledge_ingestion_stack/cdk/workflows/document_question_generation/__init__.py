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

class DocumentQuestionGenerationStack(Construct):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            pages_per_chunk: str,
            questions_per_chunk: str,
            language_code: str,
            main_jobs_table: dynamodb.Table,
            shared_utils_layer: lambda_python.PythonLayerVersion,
            **kwargs
    ) -> None:

        super().__init__(scope, construct_id, **kwargs)

        # KMS keys for this app
        self.sqs_kms_key = kms.Key(self,
                                   "QuestionGen-SQS-KMSKey",
                                   alias=f"questions-sqs-key-{Stack.of(self).stack_name}",
                                   enable_key_rotation=True
                                   )

        # A S3 bucket to store the documents
        self.docs_bucket = pace.PACEBucket(
            self,
            "RegulationBucket"
        )

        # A DynamoDB table to store the results of the processed documents
        self.jobs_table = pace.PACETable(
            self,
            "StatusTable",
            partition_key=dynamodb.Attribute(name="job_id", type=dynamodb.AttributeType.STRING),
        )

        self.jobs_table.add_global_secondary_index(
            index_name="QuestionsByAnalysisId",
            non_key_attributes=["status", "questions"],
            partition_key=dynamodb.Attribute(name="main_job_id", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.INCLUDE,
        )

        # Create a log group for the workflow
        workflow_log_group = logs.LogGroup(
            self,
            "QuestionGenWorkflowLogGroup",
            retention=logs.RetentionDays.ONE_MONTH,
            log_group_name='QuestionGenerationWorkflowLogs',
            removal_policy=aws_cdk.RemovalPolicy.DESTROY
        )

        # An Amazon SNS topic
        self.sns_topic = sns.Topic(
            self,
            "QuestionGenSNSTextractTopic",
            display_name="QuestionGen-AmazonTextract-AsyncJobsTopic",
            topic_name="QuestionGen-AmazonTextract-AsyncJobsTopic"
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
            "QuestionGenSQSTextractQueue",
            visibility_timeout=Duration.seconds(60 * 5),
            queue_name="QuestionGen-AmazonTextract-AsyncJobsQueue",
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=self.sqs_kms_key,
            enforce_ssl=True
        )

        # A dead letter SQS queue for the main SQS queue
        self.sqs_dead_letter_queue = sqs.Queue(
            self,
            "QuestionGenSQSTextractDeadLetterQueue",
            visibility_timeout=Duration.seconds(60 * 5),
            queue_name="QuestionGen-AmazonTextract-AsyncJobsDeadLetterQueue",
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
            "QuestionGenSNSTextractRole",
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
            "QuestionGenChunkDocumentLambda",
            entry=os.path.join(APP_DIR, "lambda/question_generation_workflow/chunk_textract_document_fn"),
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
            timeout=Duration.minutes(15),
            memory_size=4096
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

        # Lambda function to create questions for each chunk
        self.create_question_for_chunk_lambda = lambda_python.PythonFunction(
            self,
            "QuestionGenCreateAnalysisQuestionsLambda",
            entry=os.path.join(APP_DIR, "lambda/question_generation_workflow/create_questions_from_chunk"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "create_questions_per_chunk_lambda",
                "REGION": Stack.of(self).region,
                "BEDROCK_REGION": Stack.of(self).region,
                "BEDROCK_ACTOR_MODEL_ID": "us.amazon.nova-lite-v1:0",
                "BEDROCK_EVALUATOR_MODEL_ID": "us.amazon.nova-pro-v1:0",
                "BEDROCK_FEEDBACK_MODEL_ID": "us.amazon.nova-lite-v1:0",
                "BEDROCK_STRUCTURED_OUTPUT_MODEL_ID": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
                "LANGUAGE_ID": language_code,
                "MAX_N_QUESTIONS": questions_per_chunk,
                "REFLEXION_MIN_SCORE": "0.80",
                "MAX_TRIALS": "3",
                "JOBS_DYNAMO_DB_TABLE_NAME": self.jobs_table.table_name,
                "COMPLIANCE_DYNAMODB_TABLE_NAME": main_jobs_table.table_name,
                "DOCUMENTS_BUCKET_NAME": self.docs_bucket.bucket_name
            },
            timeout=Duration.minutes(15),
            memory_size=512
        )

        self.jobs_table.grant_read_write_data(self.create_question_for_chunk_lambda)
        main_jobs_table.grant_read_data(self.create_question_for_chunk_lambda)
        self.docs_bucket.grant_read(self.create_question_for_chunk_lambda)

        self.create_question_for_chunk_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel"
                ],
                resources=["*"],
            )
        )

        NagSuppressions.add_resource_suppressions(
            self.create_question_for_chunk_lambda,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda for creating questions for each chunk. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda for creating questions for each chunk. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        # Lambda function to create questions for the document
        self.consolidate_questions_lambda = lambda_python.PythonFunction(
            self,
            "QuestionDeduplicateCreateAnalysisQuestionsLambda",
            entry=os.path.join(APP_DIR, "lambda/question_generation_workflow/deduplicate_questions_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "create_questions_per_chunk_lambda",
                "REGION": Stack.of(self).region,
                "BEDROCK_REGION": Stack.of(self).region,
                "BEDROCK_MODEL_ID": "us.amazon.nova-pro-v1:0",
                "LANGUAGE_ID": language_code,
                "JOBS_DYNAMO_DB_TABLE_NAME": self.jobs_table.table_name,
                "COMPLIANCE_DYNAMODB_TABLE_NAME": main_jobs_table.table_name,
            },
            timeout=Duration.minutes(15),
            memory_size=1024
        )

        self.jobs_table.grant_read_write_data(self.consolidate_questions_lambda)
        main_jobs_table.grant_read_data(self.consolidate_questions_lambda)

        self.consolidate_questions_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel"
                ],
                resources=["*"],
            )
        )

        NagSuppressions.add_resource_suppressions(
            self.consolidate_questions_lambda,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda to consolidate questions of an entire document. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda to consolidate questions of an entire document. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        # Lambda function to persist questions to DynamoDB
        self.persist_questions_lambda = lambda_python.PythonFunction(
            self,
            "QuestionGenPersistQuestionsLambda",
            entry=os.path.join(APP_DIR, "lambda/question_generation_workflow/persist_questions_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "persist_questions_lambda",
                "JOBS_DYNAMO_DB_TABLE_NAME": self.jobs_table.table_name,
            },
            timeout=Duration.minutes(3),
            memory_size=512
        )

        self.jobs_table.grant_read_write_data(self.persist_questions_lambda)

        NagSuppressions.add_resource_suppressions(
            self.persist_questions_lambda,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda for persisting generated questions. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda for persisting generated questions. Policy created by CDK to expedite prototyping""",
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
                "total_pages.$": "$.Payload.total_pages",
                "is_in_chunks.$": "$.Payload.is_in_chunks",
                "is_by_page.$": "$.Payload.is_by_page",
                "chunk_keys.$": "$.Payload.chunk_keys"
            }
        )

        # Task to create questions per chunk
        create_questions_for_chunk_task = sfn_tasks.LambdaInvoke(
            self,
            'CreateQuestionsForChunkTask',
            lambda_function=self.create_question_for_chunk_lambda,
            result_selector={
                "statusCode.$": "$.Payload.statusCode",
                "document_key.$": "$.Payload.document_key",
                "document_name.$": "$.Payload.document_name",
                "job_id.$": "$.Payload.job_id",
                "questions.$": "$.Payload.body.questions"
            }
        )

        # Task to create unique questions per chunk
        create_questions_for_document_task = sfn_tasks.LambdaInvoke(
            self,
            'CreateQuestionsForDocumentTask',
            lambda_function=self.consolidate_questions_lambda,
            payload=sfn.TaskInput.from_object({
                "document_key.$": "$.[0].document_key",
                "document_name.$": "$.[0].document_name",
                "job_id.$": "$.[0].job_id",
                "questions.$": "$.[*].questions"
            }),
            result_selector={
                "statusCode.$": "$.Payload.statusCode",
                "document_key.$": "$.Payload.document_key",
                "document_name.$": "$.Payload.document_name",
                "job_id.$": "$.Payload.job_id",
                "questions.$": "$.Payload.body.questions"
            },
        )

        # Task to persist generated questions
        persist_questions_task = sfn_tasks.LambdaInvoke(
            self,
            'PersistQuestionsTask',
            lambda_function=self.persist_questions_lambda,
        )
        
        sfn_chunk_questions_map = sfn.Map(
            self,
            'ChunkQuestionIteratorMetadataMap',
            items_path='$.chunk_keys',
            item_selector={
                'chunk_index.$': '$$.Map.Item.Index',
                'chunk_s3_key.$': '$$.Map.Item.Value',
                'document_key.$': '$.document_key',
                'document_name.$': '$.document_name',
                'job_id.$': '$.job_id'
            },
            max_concurrency=5,
        )

        (sfn_chunk_questions_map.
         item_processor(create_questions_for_chunk_task).
         next(create_questions_for_document_task).
         next(persist_questions_task))
        chunk_document_task.next(sfn_chunk_questions_map)

        definition = chunk_document_task

        self.question_generation_pipeline_sfn = sfn.StateMachine(
            self,
            'QuestionGeneratorWorkflow',
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            logs=sfn.LogOptions(
                level=sfn.LogLevel.ALL,
                destination=workflow_log_group
            ),
            tracing_enabled=True
        )

        NagSuppressions.add_resource_suppressions(
            self.question_generation_pipeline_sfn,
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
            self.question_generation_pipeline_sfn,
            invocation_type=pipes_targets.StateMachineInvocationType.FIRE_AND_FORGET
        )

        self.event_bridge_pipe = pipes.Pipe(
            self,
            "QuestionGen-SQS-SFN-QuestionGeneratorPipe",
            source=pipes_sources.SqsSource(self.sqs_queue),
            target=sfn_pipe_target
        )