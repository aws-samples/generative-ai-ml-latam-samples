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
from inspect import stack

import aws_cdk
from aws_cdk import (
    Stack,
    NestedStack,
    Duration,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    aws_logs as logs,
    aws_lambda_python_alpha as lambda_python,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
)
from constructs import Construct
from cdk_nag import NagSuppressions, NagPackSuppression

class DocAnalysisSFNPipeline(NestedStack):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            dynamo_docs_table: dynamodb.Table,
            output_s3_bucket: s3.Bucket,
            shared_status_lambda_layer: lambda_python.PythonLayerVersion,
            language_code: str,
            pages_chunk: str,
            use_examples: bool,
            extraction_confidence_level: str,
            **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)
        #
        '''
        ---- Workflow definition ---
        0. Chunk file (Task state)
        1. Data extraction to custom schema (Task State)
        2. Data consolidation (Task State)
        3. Data persist (Task State)
        4. PDF report generation (Task State)
        '''

        # Shared Lambda layer with Python packaging for text information extraction
        self.shared_doc_info_layer = lambda_python.PythonLayerVersion(
            self,
            "DocInfoLayer",
            entry=os.path.join(os.path.dirname(__file__), "shared"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_13],
        )


        # Lambda function to chunk document
        self.chunk_document_lambda = lambda_python.PythonFunction(
            self,
            "ChunkDocumentLambda",
            entry="./pace_backend/text_analysis_workflow/chunk_textract_document_fn",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_status_lambda_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "chunk_document_lambda",
                "PAGE_CHUNK_SIZE":  pages_chunk,
                "DOCUMENTS_DYNAMO_DB_TABLE_NAME": dynamo_docs_table.table_name,
            },
            timeout=Duration.seconds(60),
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
        dynamo_docs_table.grant_read_write_data(self.chunk_document_lambda)

        NagSuppressions.add_resource_suppressions(
            self.chunk_document_lambda,
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

        # Lambda function to extract information from chunk
        self.extract_information_from_chunk_lambda = lambda_python.PythonFunction(
            self,
            "ExtractInformationFromChunkLambda",
            entry="./pace_backend/text_analysis_workflow/extract_data_to_schema_fn",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[self.shared_doc_info_layer, shared_status_lambda_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "information_extraction_lambda",
                "USE_EXAMPLES": str(use_examples),
                "REGION": Stack.of(self).region,
                "BEDROCK_REGION": "us-east-1",
                "BEDROCK_MODEL_ID": "us.anthropic.claude-3-haiku-20240307-v1:0", #Inference profile instead of model Id
                "LANGUAGE_ID": language_code,
                "DOCUMENTS_DYNAMO_DB_TABLE_NAME": dynamo_docs_table.table_name,
                "EXTRACTION_CONFIDENCE_LEVEL": extraction_confidence_level,
            },
            timeout=Duration.minutes(15),  # MAX VALUE, DO NOT INCREASE
        )

        self.extract_information_from_chunk_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel"
                ],
                resources=["*"],
            )
        )

        dynamo_docs_table.grant_read_write_data(self.extract_information_from_chunk_lambda)

        NagSuppressions.add_resource_suppressions(
            self.extract_information_from_chunk_lambda,
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

        # Lambda function to consildate report from individual chunks
        self.consolidate_report_lambda = lambda_python.PythonFunction(
            self,
            "ConsolidateReportLambda",
            entry="./pace_backend/text_analysis_workflow/consolidate_report_fn",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[self.shared_doc_info_layer, shared_status_lambda_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "consolidate_report_lambda",
                "REGION": Stack.of(self).region,
                "BEDROCK_REGION": "us-east-1",
                "BEDROCK_MODEL_ID": "us.anthropic.claude-3-5-sonnet-20240620-v1:0",
                "LANGUAGE_ID": language_code,
                "DOCUMENTS_DYNAMO_DB_TABLE_NAME": dynamo_docs_table.table_name,
            },
            timeout=Duration.seconds(300),
        )

        self.consolidate_report_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel"
                ],
                resources=["*"],
            )
        )

        dynamo_docs_table.grant_read_write_data(self.consolidate_report_lambda)

        NagSuppressions.add_resource_suppressions(
            self.consolidate_report_lambda,
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

        # A Lambda function to persist the results to DynamoDB
        self.persist_results_lambda = lambda_python.PythonFunction(
            self,
            "PersistResultsLambda",
            entry="./pace_backend/text_analysis_workflow/persist_results_fn",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_status_lambda_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "persist_results_lambda",
                "DOCUMENTS_DYNAMO_DB_TABLE_NAME": dynamo_docs_table.table_name,
            },
            timeout=Duration.seconds(30),
        )

        dynamo_docs_table.grant_write_data(self.persist_results_lambda)

        NagSuppressions.add_resource_suppressions(
            self.persist_results_lambda,
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

        # A Lambda function to generate PDF report
        self.generate_pdf_report_lambda = lambda_python.PythonFunction(
            self,
            "GeneratePDFReportLambda",
            entry="./pace_backend/text_analysis_workflow/generate_pdf_fn",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[self.shared_doc_info_layer, shared_status_lambda_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "generate_pdf_report_lambda",
                "REGION": Stack.of(self).region,
                "DOCUMENTS_DYNAMO_DB_TABLE_NAME": dynamo_docs_table.table_name,
                "OUTPUT_BUCKET_NAME": output_s3_bucket.bucket_name,
            },
            timeout=Duration.seconds(300),
        )

        dynamo_docs_table.grant_read_write_data(self.generate_pdf_report_lambda)
        output_s3_bucket.grant_read_write(self.generate_pdf_report_lambda)

        NagSuppressions.add_resource_suppressions(
            self.generate_pdf_report_lambda,
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

        # Create step functions tasks

        # Task to chunk documents
        chunk_document_task = sfn_tasks.LambdaInvoke(
            self,
            'ChunkDocumentTask',
            lambda_function=self.chunk_document_lambda,
            result_selector={
                "body.$": "$.Payload.body",
                "statusCode.$": "$.Payload.statusCode",
                "job_id.$": "$.Payload.job_id",
                "requestId.$": "$.SdkResponseMetadata.RequestId"
            }
        )

        # Task to extract information
        extract_data_task = sfn_tasks.LambdaInvoke(
            self,
            'ExtractData2Schema',
            lambda_function=self.extract_information_from_chunk_lambda,
            result_selector={
                "body.$": "$.Payload.body",
                "statusCode.$": "$.Payload.statusCode",
                "requestId.$": "$.SdkResponseMetadata.RequestId"
            },
            result_path="$.TaskResult"
        )

        sfn_map = sfn.Map(self,
                          'ChunkIteratorMap',
                          items_path='$.body.results.text',
                          item_selector={
                              'chunk_index.$': '$$.Map.Item.Index',
                              'text.$': '$$.Map.Item.Value',
                              'job_id.$': '$.job_id'
                          },
                          max_concurrency=5,
                          )
        sfn_map.item_processor(extract_data_task)

        # Task to consolidate results
        consolidate_report_task = sfn_tasks.LambdaInvoke(
            self,
            'ConsolidateReport',
            lambda_function=self.consolidate_report_lambda,
        )

        # Task to persist report to DynamoDB
        persist_results_task = sfn_tasks.LambdaInvoke(
            self,
            'PersistResults',
            lambda_function=self.persist_results_lambda,
        )

        # Task to generate PDF report
        generate_pdf_report_task = sfn_tasks.LambdaInvoke(
            self,
            'GeneratePDFReport',
            lambda_function=self.generate_pdf_report_lambda,
        )

        # Create step functions state machine

        chunk_document_task.next(sfn_map).next(consolidate_report_task).next(persist_results_task).next(generate_pdf_report_task)
        definition = chunk_document_task

        sfn_log_group = logs.LogGroup(
            self,
            'SfnLogGroup',
            log_group_name='ExtractionWorkflowLogs',
            removal_policy=aws_cdk.RemovalPolicy.DESTROY
        )

        self.document_processing_pipeline_sfn = sfn.StateMachine(
            self,
            'ExtractionWorkflow',
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            logs=sfn.LogOptions(
                level=sfn.LogLevel.ALL,
                destination=sfn_log_group
            ),
            tracing_enabled=True
        )

        NagSuppressions.add_resource_suppressions(
            self.document_processing_pipeline_sfn,
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