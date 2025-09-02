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

class ComplianceReportStack(Construct):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            language_code: str,
            compliance_analysis_jobs_table: dynamodb.Table,
            question_jobs_table: dynamodb.Table,
            reports_bucket: s3.Bucket,
            shared_utils_layer: lambda_python.PythonLayerVersion,
            **kwargs
    ) -> None:

        super().__init__(scope, construct_id, **kwargs)

        # Create a log group for the workflow
        workflow_log_group = logs.LogGroup(
            self,
            "ComplianceReportWorkflowLogGroup",
            retention=logs.RetentionDays.ONE_MONTH,
            log_group_name='ComplianceReportWorkflowLogs',
            removal_policy=aws_cdk.RemovalPolicy.DESTROY
        )

        ########################------------------LAMBDA FUNCTIONS-------------------#######################

        # Lambda function to create question set for compliance analysis
        self.create_question_set = lambda_python.PythonFunction(
            self,
            "ComplianceQuestionSetLambda",
            entry=os.path.join(APP_DIR, "lambda/regulation_compliance_analysis_workflow/get_question_set_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "create_question_set_lambda",
                "REGION": Stack.of(self).region,
                "LANGUAGE_ID": language_code,
                "MAX_QUESTIONS_TOKEN_COUNT": "500",
                "QUESTION_JOBS_DYNAMODB_TABLE_NAME": question_jobs_table.table_name,
                "COMPLIANCE_JOBS_DYNAMODB_TABLE_NAME": compliance_analysis_jobs_table.table_name
            },
            timeout=Duration.minutes(1),
            memory_size=128
        )

        question_jobs_table.grant_read_write_data(self.create_question_set)
        compliance_analysis_jobs_table.grant_read_write_data(self.create_question_set)

        NagSuppressions.add_resource_suppressions(
            self.create_question_set,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda question chunking. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda question chunking. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        # Lambda function to map questions to report section
        self.map_question_set_to_report = lambda_python.PythonFunction(
            self,
            "MapQuestionSetToReportLambda",
            entry=os.path.join(APP_DIR, "lambda/regulation_compliance_analysis_workflow/map_questions_to_template_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "create_question_set_lambda",
                "REGION": Stack.of(self).region,
                "BEDROCK_REGION": Stack.of(self).region,
                "BEDROCK_MODEL_ID": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                "LANGUAGE_ID": language_code,
                "COMPLIANCE_JOBS_DYNAMODB_TABLE_NAME": compliance_analysis_jobs_table.table_name,
                "COMPLIANCE_REPORTS_BUCKET_NAME": reports_bucket.bucket_name
            },
            timeout=Duration.minutes(15),
            memory_size=512
        )

        self.map_question_set_to_report.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel"
                ],
                resources=["*"],
            )
        )

        compliance_analysis_jobs_table.grant_read_write_data(self.map_question_set_to_report)
        reports_bucket.grant_read_write(self.map_question_set_to_report)

        NagSuppressions.add_resource_suppressions(
            self.map_question_set_to_report,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda question mapping to section. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda question mapping to section. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        # Lambda function to consolidate a unified report template
        self.consolidate_report_template = lambda_python.PythonFunction(
            self,
            "ConsolidateReportTemplateLambda",
            entry=os.path.join(APP_DIR, "lambda/regulation_compliance_analysis_workflow/generate_report_with_questions_fn"),
            index="index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "POWERTOOLS_SERVICE_NAME": "create_question_set_lambda",
                "REGION": Stack.of(self).region,
                "COMPLIANCE_JOBS_DYNAMODB_TABLE_NAME": compliance_analysis_jobs_table.table_name,
                "COMPLIANCE_REPORTS_BUCKET_NAME": reports_bucket.bucket_name
            },
            timeout=Duration.minutes(1),
            memory_size=128
        )

        compliance_analysis_jobs_table.grant_read_write_data(self.consolidate_report_template)
        reports_bucket.grant_read(self.consolidate_report_template)

        NagSuppressions.add_resource_suppressions(
            self.consolidate_report_template,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda question mapping consolidation to section. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda question mapping consolidation to section. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        # Lambda function to extract metadata from chunk

        ########################------------------LAMBDA FUNCTIONS-------------------#######################

        #######################------------------STEP FUNCTIONS WORKFLOW-------------#######################

        # Create step functions tasks

        # Task to chunk questions
        chunk_questions_task = sfn_tasks.LambdaInvoke(
            self,
            'ChunkQuestionsTask',
            lambda_function=self.create_question_set,
            result_selector={
                "statusCode.$": "$.Payload.statusCode",
                "job_id.$": "$.Payload.job_id",
                "questions.$": "$.Payload.body.question_chunks",
                "report_template.$": "$.Payload.body.report_template",
            }
        )

        # Task to map questions to section
        map_questions_to_report_task = sfn_tasks.LambdaInvoke(
            self,
            'MapQuestionsTask',
            lambda_function=self.map_question_set_to_report,
            result_selector={
                "statusCode.$": "$.Payload.statusCode",
                "job_id.$": "$.Payload.job_id",
                "report_template.$": "$.Payload.body.report_template",
            }
        )

        # Task to consolidate question map to section
        consolidate_questions_to_report_task = sfn_tasks.LambdaInvoke(
            self,
            'ConsolidateQuestionsTask',
            lambda_function=self.consolidate_report_template,
        )

        sfn_questions_report_map = sfn.Map(
            self,
            'ChunkIteratorQAMap',
            items_path='$.questions',
            item_selector={
                'question_chunk_index.$': '$$.Map.Item.Index',
                'question_set.$': '$$.Map.Item.Value',
                'job_id.$': '$.job_id',
                'report_template.$': '$.report_template'
            },
            max_concurrency=5,
        )

        sfn_questions_report_map.item_processor(map_questions_to_report_task)
        definition = chunk_questions_task.next(sfn_questions_report_map).next(consolidate_questions_to_report_task)

        self.compliance_report_pipeline_sfn = sfn.StateMachine(
            self,
            'ComplianceReportAnalysisWorkflow',
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            logs=sfn.LogOptions(
                level=sfn.LogLevel.ALL,
                destination=workflow_log_group
            ),
            tracing_enabled=True
        )

        NagSuppressions.add_resource_suppressions(
            self.compliance_report_pipeline_sfn,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for compliance analysis workflow. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for compliance analysis workflow. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        #######################------------------STEP FUNCTIONS WORKFLOW-------------#######################