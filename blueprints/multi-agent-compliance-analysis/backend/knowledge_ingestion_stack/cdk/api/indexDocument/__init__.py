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
    CfnOutput,
    aws_apigateway as apigw,
    aws_sns as sns,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_cognito as cognito,
    aws_logs as logs,
    aws_s3 as s3,
    aws_lambda_python_alpha as lambda_python,
    aws_lambda as lambda_,
    aws_wafv2 as waf,
    Duration,
)
from constructs import Construct
from cdk_nag import NagSuppressions

APP_DIR = os.path.join(os.path.dirname(__file__), "../../..", "app")
API_PREFIX = "compliance-report/data-indexing"

from .process_document import ProcessDocument
from .get_jobs import GetJobs
from .get_presigned_s3_url import GetPresignedS3URL

class IndexDocumentAPI(Construct):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            document_bucket: s3.IBucket,
            jobs_table: dynamodb.ITable,
            sns_textract_topic: sns.ITopic,
            sns_textract_role: iam.IRole,
            shared_utils_layer: lambda_python.PythonLayerVersion,
            cognitoUserPool: cognito.IUserPool,
    ) -> None:

        super().__init__(scope, construct_id)

        self.api_access_log_group = logs.LogGroup(
            self,
            "IndexDocumentApiAccessLogGroup",
            retention=logs.RetentionDays.ONE_MONTH
        )

        # REST API
        self.api = apigw.RestApi(
            self,
            "IndexDocumentsApi",
            rest_api_name="Index Documents LLM",
            description="API for indexing documents into knowledge base using LLMs",
            cloud_watch_role=True,
            endpoint_configuration=apigw.EndpointConfiguration(
                types=[apigw.EndpointType.EDGE]
            ),
            deploy_options=apigw.StageOptions(
                logging_level=apigw.MethodLoggingLevel.INFO,
                access_log_destination=apigw.LogGroupLogDestination(
                    self.api_access_log_group
                ),
                access_log_format=apigw.AccessLogFormat.clf(),
                tracing_enabled=True,
            ),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=apigw.Cors.DEFAULT_HEADERS,
            ),
        )

        self.validator = apigw.RequestValidator(
            self,
            "backend-api-validator",
            rest_api=self.api,
            request_validator_name="Validate body and query string parameters",
            validate_request_body=True,
            validate_request_parameters=True,
        )

        cognito_authorizer = apigw.CognitoUserPoolsAuthorizer(
            self,
            "CognitoUserPoolAuthorizer-Index",
            cognito_user_pools=[cognitoUserPool],
        )


        ######################-----------------LAMBDA FUNCTIONS---------------------######################

        # A lambda function to start the text extraction process
        self.start_text_extraction_lambda = lambda_python.PythonFunction(
            self,
            "StartTextExtractionLambda",
            entry=os.path.join(APP_DIR, "lambda/api/indexDocument/start_text_extraction_fn"),
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "JOBS_DYNAMO_DB_TABLE_NAME": jobs_table.table_name,
                "TEXTRACT_SNS_TOPIC_ARN": sns_textract_topic.topic_arn,
                "TEXTRACT_SNS_ROLE_ARN": sns_textract_role.role_arn,
                "DOCUMENTS_BUCKET_NAME": document_bucket.bucket_name,
            },
            timeout=Duration.seconds(60),
        )
        self.start_text_extraction_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "textract:StartDocumentTextDetection",
                    "textract:GetDocumentTextDetection"
                ],
                resources=["*"],
            )
        )
        document_bucket.grant_read(self.start_text_extraction_lambda)
        jobs_table.grant_write_data(self.start_text_extraction_lambda)

        NagSuppressions.add_resource_suppressions(
            self.start_text_extraction_lambda,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda text detection function. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda text detection function. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        # A Lambda function to get the status of the current jobs
        self.get_processing_jobs_lambda = lambda_python.PythonFunction(
            self,
            "GetIndexingJobsStatusLambda",
            entry=os.path.join(APP_DIR, "lambda/api/indexDocument/get_job_status_fn"),
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            environment={
                "JOBS_DYNAMO_DB_TABLE_NAME": jobs_table.table_name,
            },
            timeout=Duration.seconds(60),
        )
        jobs_table.grant_read_data(self.get_processing_jobs_lambda)

        NagSuppressions.add_resource_suppressions(
            self.get_processing_jobs_lambda,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda for getting job status function. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda for getting job status function. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        # A Lambda function to obtain a pre-signed URL
        self.get_presigned_s3_url_lambda = lambda_python.PythonFunction(
            self,
            "GetPresignedS3URLLambda",
            entry=os.path.join(APP_DIR, "lambda/api/indexDocument/get_presigned_s3_url_fn"),
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            environment={
                "DOCUMENTS_BUCKET_NAME": document_bucket.bucket_name,
            },
            timeout=Duration.seconds(60),
        )
        document_bucket.grant_read_write(self.get_presigned_s3_url_lambda)

        NagSuppressions.add_resource_suppressions(
            self.get_presigned_s3_url_lambda,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda for getting a pre-signed URL. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda for getting a pre-signed URL. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        ######################-----------------LAMBDA FUNCTIONS---------------------######################

        ######################-----------------API METHODS---------------------######################

        # Method for starting the processing of a document
        ProcessDocument(
            self,
            "ProcessDocumentMethod",
            api = self.api,
            cognito_authorizer = cognito_authorizer,
            resource_path = f"{API_PREFIX}/processDocument",
            http_method = "POST",
            request_validator = self.validator,
            lambda_function = self.start_text_extraction_lambda,
            request_parameters={
                "method.request.header.Accept": True,
                "method.request.header.Content-Type": True,
            },
        )

        # Method for getting the status of all the indexing jobs
        GetJobs(
            self,
            "GetIndexingJobsMethod",
            api=self.api,
            cognito_authorizer=cognito_authorizer,
            resource_path=f"{API_PREFIX}/jobs",
            http_method="GET",
            request_validator=self.validator,
            lambda_function=self.get_processing_jobs_lambda,
        )

        # Method for getting a presigned URL to upload a document
        GetPresignedS3URL(
            self,
            "GetPresignedS3URLMethod",
            api=self.api,
            cognito_authorizer=cognito_authorizer,
            resource_path=f"{API_PREFIX}/upload/{{folder}}/{{key}}",
            http_method="GET",
            request_validator=self.validator,
            lambda_function=self.get_presigned_s3_url_lambda
        )

        ######################-----------------API METHODS---------------------######################

        # Associate a WAF with the deployment stage
        self.web_acl = waf.CfnWebACL(
            self,
            "WebACL",
            scope="REGIONAL",
            default_action=waf.CfnWebACL.DefaultActionProperty(
                allow=waf.CfnWebACL.AllowActionProperty(),
            ),
            visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                sampled_requests_enabled=True,
                metric_name=construct_id + "-WebACL",
            ),
            rules=[
                waf.CfnWebACL.RuleProperty(
                    name="AWSManagedRules",
                    priority=0,
                    statement=waf.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=waf.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesCommonRuleSet",
                            excluded_rules=[],
                        )
                    ),
                    override_action=waf.CfnWebACL.OverrideActionProperty(
                        none={},
                    ),
                    visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        sampled_requests_enabled=True,
                        metric_name=construct_id + "-WebACL-AWSManagedRules",
                    ),
                )
            ],
        )

        self.web_acl_assoc = waf.CfnWebACLAssociation(
            self,
            "WebACLAssociation",
            web_acl_arn=self.web_acl.attr_arn,
            resource_arn="arn:aws:apigateway:{}::/restapis/{}/stages/{}".format(
                Stack.of(self).region,
                self.api.rest_api_id,
                self.api.deployment_stage.stage_name,
            ),
        )

        NagSuppressions.add_resource_suppressions(
            self.api,
            [
                {
                    "id": "AwsSolutions-COG4",
                    "reason": "The OPTIONS method for CORS should not use authorization.",
                },
                {
                    "id": "AwsSolutions-APIG4",
                    "reason": "The OPTIONS method for CORS should not use authorization.",
                },
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Prototype will use managed policies to expedite development. 
                            TODO: Replace on Production environment (Path to Production)""",
                    "appliesTo": [
                        "Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs",
                    ],
                },
            ],
            True,
        )