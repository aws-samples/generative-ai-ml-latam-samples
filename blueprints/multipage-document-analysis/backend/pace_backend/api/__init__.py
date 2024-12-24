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

from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    aws_sns as sns,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_kms as kms,
    aws_logs as logs,
    aws_s3 as s3,
    aws_lambda_python_alpha as lambda_python,
    aws_lambda as lambda_,
    aws_wafv2 as waf,
    Duration,
)
from constructs import Construct
from cdk_nag import NagSuppressions

from pace_constructs.pace_cognito import PACECognito

from .process_document import ProcessDocument
from .get_result import GetResult
from .get_jobs import GetJobs
from .get_job_details import GetJobDetails
from .get_presigned_s3_url import GetPresignedS3URL

class DocumentAPI(Construct):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            document_bucket: s3.IBucket,
            report_bucket: s3.IBucket,
            documents_table: dynamodb.ITable,
            sns_textract_topic: sns.ITopic,
            sns_textract_role: iam.IRole,
            shared_status_lambda_layer: lambda_python.PythonLayerVersion,
    ) -> None:

        super().__init__(scope, construct_id)

        # Cognito user pool to authenticate APIs
        self.cognito = PACECognito(
            self,
            "Cognito",
            region=Stack.of(self).region,
        )

        self.authorizer = apigw.CognitoUserPoolsAuthorizer(
            self,
            "CognitoAuthorizer",
            cognito_user_pools=[self.cognito.user_pool],
            authorizer_name=Stack.of(self).stack_name + "-authorizer",
        )

        self.api_access_log_group = logs.LogGroup(
            self, "ApiAccessLogGroup", retention=logs.RetentionDays.ONE_MONTH
        )

        # REST API
        self.api = apigw.RestApi(
            self,
            "DocumentsApi",
            rest_api_name="Document Analysis LLM",
            description="API for Analyzing Multipage Documents usins LLMs",
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

        ###### Lambda functions

        # A lambda function to start the text extraction process
        self.start_text_extraction_lambda = lambda_python.PythonFunction(
            self,
            "StartTextExtractionLambda",
            entry="./pace_backend/api/lambda/start_text_extraction_fn",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_status_lambda_layer],
            environment={
                "DOCUMENTS_DYNAMO_DB_TABLE_NAME": documents_table.table_name,
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
        documents_table.grant_write_data(self.start_text_extraction_lambda)

        NagSuppressions.add_resource_suppressions(
            self.start_text_extraction_lambda,
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

        # A Lambda function to get the status of the current jobs
        self.get_processing_jobs_lambda = lambda_python.PythonFunction(
            self,
            "GetJobsStatusLambda",
            entry="./pace_backend/api/lambda/get_job_status_fn",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            environment={
                "DOCUMENTS_DYNAMO_DB_TABLE_NAME": documents_table.table_name,
            },
            timeout=Duration.seconds(60),
        )
        documents_table.grant_read_data(self.get_processing_jobs_lambda)

        NagSuppressions.add_resource_suppressions(
            self.get_processing_jobs_lambda,
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

        # A Lambda function to get the details of a processing job
        self.lambda_get_job_details = lambda_python.PythonFunction(
            self,
            "GetJobDetailsLambda",
            entry="./pace_backend/api/lambda/get_job_details_fn",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_status_lambda_layer],
            environment={
                "DOCUMENTS_DYNAMO_DB_TABLE_NAME": documents_table.table_name,
            },
            timeout=Duration.seconds(60),
        )
        documents_table.grant_read_data(self.lambda_get_job_details)

        NagSuppressions.add_resource_suppressions(
            self.lambda_get_job_details,
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

        # A Lambda function to retrieve the results of the document processing
        self.lambda_get_results = lambda_python.PythonFunction(
            self,
            "GetResultsLambda",
            entry="./pace_backend/api/lambda/get_job_results_fn",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_status_lambda_layer],
            environment={
                "DOCUMENTS_DYNAMO_DB_TABLE_NAME": documents_table.table_name,
            },
            timeout=Duration.seconds(60),
        )
        documents_table.grant_read_data(self.lambda_get_results)

        NagSuppressions.add_resource_suppressions(
            self.lambda_get_results,
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

        # A Lambda function to get presigned urls for documents
        self.lambda_get_presigned_url = lambda_python.PythonFunction(
            self,
            "GetPresignedUrlLambda",
            entry="./pace_backend/api/lambda/get_presigned_s3_url_fn",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            environment={
                "REGION": Stack.of(self).region,
                "DOCUMENTS_BUCKET_NAME": document_bucket.bucket_name,
                "REPORTS_BUCKET_NAME": report_bucket.bucket_name
            },
            timeout=Duration.seconds(60),
        )
        document_bucket.grant_read_write(self.lambda_get_presigned_url)
        report_bucket.grant_read(self.lambda_get_presigned_url)

        NagSuppressions.add_resource_suppressions(
            self.lambda_get_presigned_url,
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

        # API methods

        # Method for uploading documents
        GetPresignedS3URL(
            self,
            "UploadDocumentMethod",
            api = self.api,
            cognito_authorizer= self.authorizer,
            resource_path = "/multipage-doc-analysis/upload/{folder}/{key}",
            http_method = "GET",
            request_validator = self.validator,
            lambda_function = self.lambda_get_presigned_url
        )

        # Method for downloading documents
        GetPresignedS3URL(
            self,
            "DownloadDocumentMethod",
            api = self.api,
            cognito_authorizer= self.authorizer,
            resource_path = "/multipage-doc-analysis/download/{docType}/{folder}/{key}",
            http_method = "GET",
            request_validator = self.validator,
            lambda_function = self.lambda_get_presigned_url
        )

        # Method for starting the processing of a document
        ProcessDocument(
            self,
            "ProcessDocumentMethod",
            api = self.api,
            cognito_authorizer= self.authorizer,
            resource_path = "multipage-doc-analysis/processDocument",
            http_method = "POST",
            request_validator = self.validator,
            lambda_function = self.start_text_extraction_lambda,
            request_parameters={
                "method.request.header.Accept": True,
                "method.request.header.Content-Type": True,
            },
        )

        GetJobs(
            self,
            "GetJobsMethod",
            api=self.api,
            cognito_authorizer=self.authorizer,
            resource_path="multipage-doc-analysis/jobs",
            http_method="GET",
            request_validator=self.validator,
            lambda_function=self.get_processing_jobs_lambda,
        )

        GetJobDetails(
            self,
            "GetJobDetailsMethod",
            api=self.api,
            cognito_authorizer=self.authorizer,
            resource_path="multipage-doc-analysis/jobs",
            http_method="GET",
            request_validator=self.validator,
            lambda_function=self.lambda_get_job_details
        )

        GetResult(
            self,
            "GetResultMethod",
            api=self.api,
            cognito_authorizer=self.authorizer,
            resource_path="multipage-doc-analysis/jobs",
            http_method="GET",
            request_validator=self.validator,
            lambda_function=self.lambda_get_results
        )

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
