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
    Size,
    aws_ecr_assets as cdk_ecr_assets,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    aws_iam as iam,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_ssm as ssm,
    aws_sqs as sqs,
    aws_kms as kms,
    aws_s3 as s3,
    aws_ecs_patterns as ecs_patterns
)

import pace_constructs as pace

from constructs import Construct

from cdk_nag import NagSuppressions

APP_DIR = os.path.join(os.path.dirname(__file__), "../../", "app")

class MultiAgentComplianceAnalysis(Construct):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            dynamod_db_jobs_table: dynamodb.Table,
            sqs_fargate_queue: sqs.Queue,
            kms_sqs_key: kms.Key,
            reports_s3_bucket: s3.Bucket,
            lawyer_agent_arn: str,
            writer_agent_arn: str,
            auditor_agent_arn: str,
            **kwargs
    ) -> None:

        super().__init__(scope, construct_id, **kwargs)

        # Add agent ARNs as parameters with unique names
        stack_name = Stack.of(self).stack_name
        
        self.lawyer_agent_arn_parameter = ssm.StringParameter(
            self,
            "LawyerAgentARNParameter",
            parameter_name=f"/{stack_name}/agents/lawyer-agent-arn",
            string_value=lawyer_agent_arn,
            description="ARN of the AgentCore Lawyer agent"
        )

        self.auditor_agent_arn_parameter = ssm.StringParameter(
            self,
            "AuditorAgentARNParameter",
            parameter_name=f"/{stack_name}/agents/auditor-agent-arn",
            string_value=auditor_agent_arn,
            description="ARN of the AgentCore Auditor agent"
        )

        self.writer_agent_arn_parameter = ssm.StringParameter(
            self,
            "WriterAgentARNParameter",
            parameter_name=f"/{stack_name}/agents/writer-agent-arn",
            string_value=writer_agent_arn,
            description="ARN of the AgentCore Writer agent"
        )

        self.dynamodb_name_parameter = ssm.StringParameter(
            self,
            "DynamoDBTableNameParameter",
            parameter_name=f"/{Stack.of(self).stack_name}/dynamoTables/compliance-analysis-dynamo-db-table-name",
            string_value=dynamod_db_jobs_table.table_name,
            description="DynamoDB table name of the compliance analysis table"
        )

        self.s3_bucket_name_parameter = ssm.StringParameter(
            self,
            "S3BucketNameParameter",
            parameter_name=f"/{Stack.of(self).stack_name}/s3buckets/compliance-analysis-s3-reports-bucket-name",
            string_value=reports_s3_bucket.bucket_name,
            description="S3 bucket name of the compliance reports bucket"
        )

        # Create a log group for the fargate task
        fargate_log_group = logs.LogGroup(
            self,
            "FargateComplianceAnalysisLogGroup",
            retention=logs.RetentionDays.ONE_MONTH,
            log_group_name='FargateComplianceAnalysisWorkflowLogs',
            removal_policy=aws_cdk.RemovalPolicy.DESTROY
        )

        fargate_vpc = ec2.Vpc(self, "VPCFargateComplianceAnalysis", max_azs=2)  # default is all AZs in region

        # Create VPC Flow Log
        vpc_flow_log_group = logs.LogGroup(
            self,
            "VPCFlowLogGroup",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=aws_cdk.RemovalPolicy.DESTROY
        )

        ec2.FlowLog(
            self,
            "VPCFlowLog",
            resource_type=ec2.FlowLogResourceType.from_vpc(fargate_vpc),
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(vpc_flow_log_group)
        )

        # Add DynamoDB VPC endpoint
        dynamodb_vpc_endpoint = fargate_vpc.add_gateway_endpoint(
            "DynamoDbEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB
        )

        # Add S3 VPC endpoint
        s3_vpc_endpoint = fargate_vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3
        )

        fargate_cluster = ecs.Cluster(
            self,
            "FargateComplianceAnalysisCluster",
            vpc=fargate_vpc,
            container_insights=True
        )

        self.queue_processing_fargate_service = ecs_patterns.QueueProcessingFargateService(
            self, "FargateComplianceAnalysisService",
            cluster=fargate_cluster,
            queue=sqs_fargate_queue,
            memory_limit_mib=1024,
            image=ecs.ContainerImage.from_asset(
                directory=os.path.join(APP_DIR, "regulation_compliance_analysis/compliance_report_task"),
                platform=cdk_ecr_assets.Platform.LINUX_AMD64
            ),
            command=[
                "python", "-u", "compliance_analysis/multi_agent_compliance_report.py"
            ],
            enable_logging=True,
            secrets={
                # Reference a specific version of the secret by its version id or version stage (requires platform version 1.4.0 or later for Fargate tasks)
                "AUDITOR_AGENT_ARN": ecs.Secret.from_ssm_parameter(self.auditor_agent_arn_parameter),
                "LAWYER_AGENT_ARN": ecs.Secret.from_ssm_parameter(self.lawyer_agent_arn_parameter),
                "WRITER_AGENT_ARN": ecs.Secret.from_ssm_parameter(self.writer_agent_arn_parameter),
                "JOBS_DYNAMOD_DB_NAME": ecs.Secret.from_ssm_parameter(self.dynamodb_name_parameter),
                "S3_BUCKET_NAME": ecs.Secret.from_ssm_parameter(self.s3_bucket_name_parameter)
            },
            max_scaling_capacity=5,
            container_name="ComplianceAnalysis",
            min_healthy_percent=70,
            log_driver=ecs.LogDrivers.aws_logs(
                stream_prefix="ComplianceAnalysis",
                log_group=fargate_log_group,
                mode=ecs.AwsLogDriverMode.NON_BLOCKING,
                max_buffer_size=Size.mebibytes(25)
            )
        )

        dynamod_db_jobs_table.grant_read_write_data(self.queue_processing_fargate_service.task_definition.task_role)
        reports_s3_bucket.grant_read_write(self.queue_processing_fargate_service.task_definition.task_role)
        kms_sqs_key.grant_decrypt(self.queue_processing_fargate_service.task_definition.task_role)

        self.queue_processing_fargate_service.task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock-agentcore:InvokeAgentRuntime",
                ],
                resources=[
                    lawyer_agent_arn,
                    f"{lawyer_agent_arn}/*",
                    auditor_agent_arn,
                    f"{auditor_agent_arn}/*",
                    writer_agent_arn,
                    f"{writer_agent_arn}/*",
                ]
            )
        )

        NagSuppressions.add_resource_suppressions(
            self.queue_processing_fargate_service,
            [
                {
                    "id": "AwsSolutions-ECS2",
                    "reason": """Only environment variable create is automatically created by QueueProcessingFargateService which is the SQS queue name""",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """CDK generated policy. Used to allow the fargate job access to the bucket to place objects""",
                }
            ],
            True
        )

        NagSuppressions.add_resource_suppressions(
            self.queue_processing_fargate_service.task_definition.execution_role,
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Created by QueueProcessingFargateService. Using it to expedite prototype. Adding recommendation in P2P""",
                }
            ],
            True
        )