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
    aws_sqs as sqs,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_cognito as cognito,
    aws_logs as logs,
    aws_s3 as s3,
    aws_stepfunctions as sfn,
    aws_lambda_python_alpha as lambda_python,
    aws_lambda as lambda_,
    aws_wafv2 as waf,
    Duration,
)
from constructs import Construct
from cdk_nag import NagSuppressions

APP_DIR = os.path.join(os.path.dirname(__file__), "../../..", "app")
API_PREFIX = "compliance-report"

from .create_job import CreateJob
from .generate_report_layout import CreateReportLayout
from .get_jobs import GetJobs
from .get_presigned_s3_url import GetPresignedS3URL
from .get_job_details import GetJobDetails
from .store_question_set import PutQuestionSet
from .start_compliance_analysis import StartComplianceAnalysis

class ComplianceReportsAPI(Construct):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            document_bucket: s3.IBucket,
            compliance_analysis_jobs_table: dynamodb.ITable,
            start_analysis_sqs_queue: sqs.Queue,
            report_layout_workflow_machine: sfn.IStateMachine,
            shared_utils_layer: lambda_python.PythonLayerVersion,
            cognitoUserPool: cognito.IUserPool,
    ) -> None:

        super().__init__(scope, construct_id)

        self.api_access_log_group = logs.LogGroup(
            self,
            "ComplianceReportApiAccessLogGroup",
            retention=logs.RetentionDays.ONE_MONTH
        )

        # REST API
        self.api = apigw.RestApi(
            self,
            "ComplianceReportApi",
            rest_api_name="Generate Compliance Report from Regulation LLM",
            description="API for generating compliance report from regulation documents using LLMs",
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
            "backend-compliance-report-api-validator",
            rest_api=self.api,
            request_validator_name="Validate body and query string parameters",
            validate_request_body=True,
            validate_request_parameters=True,
        )

        cognito_authorizer = apigw.CognitoUserPoolsAuthorizer(
            self,
            "CognitoUserPoolAuthorizer-ComplianceReport",
            cognito_user_pools=[cognitoUserPool],
        )

        # Create method for creating report layout
        self.api_role = iam.Role(
            self, "ApiRole", assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com")
        )


        ######################-----------------LAMBDA FUNCTIONS---------------------######################

        # A lambda function to start the text extraction process
        self.create_job_lambda = lambda_python.PythonFunction(
            self,
            "ComplianceReportCreateJob",
            entry=os.path.join(APP_DIR, "lambda/api/complianceReport/create_job_fn"),
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "JOBS_DYNAMO_DB_TABLE_NAME": compliance_analysis_jobs_table.table_name,
            },
            timeout=Duration.seconds(60),
        )
        compliance_analysis_jobs_table.grant_write_data(self.create_job_lambda)

        NagSuppressions.add_resource_suppressions(
            self.create_job_lambda,
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

        # A lambda function to store a user-defined question set
        self.store_template_questions = lambda_python.PythonFunction(
            self,
            "ComplianceReportPutQuestionSet",
            entry=os.path.join(APP_DIR, "lambda/api/complianceReport/store_questions_fn"),
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "JOBS_DYNAMO_DB_TABLE_NAME": compliance_analysis_jobs_table.table_name,
            },
            timeout=Duration.seconds(60),
        )
        compliance_analysis_jobs_table.grant_write_data(self.store_template_questions)

        NagSuppressions.add_resource_suppressions(
            self.store_template_questions,
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
            "ComplianceReportJobsStatusLambda",
            entry=os.path.join(APP_DIR, "lambda/api/complianceReport/get_job_status_fn"),
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            environment={
                "JOBS_DYNAMO_DB_TABLE_NAME": compliance_analysis_jobs_table.table_name,
            },
            timeout=Duration.seconds(60),
        )
        compliance_analysis_jobs_table.grant_read_data(self.get_processing_jobs_lambda)

        NagSuppressions.add_resource_suppressions(
            self.get_processing_jobs_lambda,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda foe getting job status function. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda foe getting job status function. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        # A Lambda function to get the details of a job
        self.get_job_details_lambda = lambda_python.PythonFunction(
            self,
            "ComplianceReportJobsDetailsLambda",
            entry=os.path.join(APP_DIR, "lambda/api/complianceReport/get_job_details_fn"),
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            layers=[shared_utils_layer],
            environment={
                "JOBS_DYNAMO_DB_TABLE_NAME": compliance_analysis_jobs_table.table_name,
            },
            timeout=Duration.seconds(60),
        )
        compliance_analysis_jobs_table.grant_read_data(self.get_job_details_lambda)

        NagSuppressions.add_resource_suppressions(
            self.get_job_details_lambda,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Service role for lambda foe getting job details function. Policy created by CDK to expedite prototyping""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for lambda foe getting job details function. Policy created by CDK to expedite prototyping""",
                },
            ],
            True
        )

        # A Lambda function to get presigned urls for documents
        self.lambda_get_presigned_url = lambda_python.PythonFunction(
            self,
            "ComplianceReportGetPresignedUrlLambda",
            entry=os.path.join(APP_DIR, "lambda/api/complianceReport/get_presigned_s3_url_fn"),
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            environment={
                "REGION": Stack.of(self).region,
                "REPORTS_BUCKET_NAME": document_bucket.bucket_name,
            },
            timeout=Duration.seconds(60),
        )
        document_bucket.grant_read_write(self.lambda_get_presigned_url)

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

        ######################-----------------LAMBDA FUNCTIONS---------------------######################

        ######################-----------------API METHODS---------------------######################

        # Method for starting the processing of a document
        CreateJob(
            self,
            "ComplianceReportCreateJobMethod",
            api = self.api,
            cognito_authorizer = cognito_authorizer,
            resource_path = f"{API_PREFIX}/createAnalysisJob",
            http_method = "POST",
            request_validator = self.validator,
            lambda_function = self.create_job_lambda,
        )

        # Method for generating presigned post
        GetPresignedS3URL(
            self,
            "ComplianceReportDownloadDocumentMethod",
            api = self.api,
            cognito_authorizer = cognito_authorizer,
            resource_path = f"/{API_PREFIX}/report/{{key}}",
            http_method = "GET",
            request_validator = self.validator,
            lambda_function = self.lambda_get_presigned_url
        )

        # Method for obtaining all jobs information
        GetJobs(
            self,
            "ComplianceReportJobsMethod",
            api=self.api,
            cognito_authorizer=cognito_authorizer,
            resource_path=f"{API_PREFIX}/jobs",
            http_method="GET",
            request_validator=self.validator,
            lambda_function=self.get_processing_jobs_lambda,
        )

        # Method for obtaining a job detailed information
        GetJobDetails(
            self,
            "ComplianceReportJobDetailsMethod",
            api=self.api,
            cognito_authorizer=cognito_authorizer,
            resource_path=f"{API_PREFIX}/jobs",
            http_method="GET",
            request_validator=self.validator,
            lambda_function=self.get_job_details_lambda,
        )

        # Method for creating an empty report
        PutQuestionSet(
            self,
            "PutQuestionSetReportMethod",
            api = self.api,
            cognito_authorizer = cognito_authorizer,
            resource_path = f"{API_PREFIX}/storeQuestions",
            http_method = "PUT",
            request_validator = self.validator,
            lambda_function = self.store_template_questions,
        )

        # Method for creating a layout of the compliance report
        CreateReportLayout(
            self,
            "ComplianceReportGenerateReportLayoutMethod",
            api = self.api,
            cognito_authorizer = cognito_authorizer,
            request_validator = self.validator,
            resource_path=f"{API_PREFIX}/reportLayout",
            api_role=self.api_role,
            workflow_machine=report_layout_workflow_machine,
        )

        #Method for starting a compliance analysis job through SQS
        StartComplianceAnalysis(
            self,
            "ComplianceReporStartAnalysisMethod",
            api=self.api,
            cognito_authorizer=cognito_authorizer,
            request_validator=self.validator,
            resource_path=f"{API_PREFIX}/startAnalysis",
            api_role=self.api_role,
            sqs_queue=start_analysis_sqs_queue
        )


        ######################-----------------API METHODS---------------------######################

        # Associate a WAF with the deployment stage
        self.web_acl = waf.CfnWebACL(
            self,
            "ComplianceReport-WebACL",
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
                            rule_action_overrides=[
                                waf.CfnWebACL.RuleActionOverrideProperty(
                                    name="SizeRestrictions_BODY",
                                    action_to_use=waf.CfnWebACL.RuleActionProperty(
                                        allow={} # Override to Allow action to allow for large bodies to be passed
                                    )
                                )
                            ]
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
            "QuestionGen-WebACLAssociation",
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