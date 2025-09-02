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

from cdklabs.generative_ai_cdk_constructs import (
    opensearchserverless,
    opensearch_vectorindex
)
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    CfnParameter,
    Fn,
    aws_dynamodb as dynamodb,
    aws_kms as kms,
    aws_sqs as sqs,
    aws_ssm as ssm,
    aws_s3 as s3
)

from constructs import Construct
from cdk_nag import NagSuppressions

from multiagent_compliance_analysis import MultiAgentComplianceAnalysis


import pace_constructs as pace

APP_DIR = os.path.join(os.path.dirname(__file__), "..", "app")


class BackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        KnowledgeIngestionStackName = CfnParameter(
            self,
            "KnowledgeIngestionStackName",
            type="String",
            description="The name of the knowledge ingestion stack",
        )

        lawyerAgentARN = CfnParameter(
            self,
            "lawyerAgentARN",
            type="String",
            description="The ARN of the AgentCore Lawyer agent"
        )

        auditorAgentARN = CfnParameter(
            self,
            "auditorAgentARN",
            type="String",
            description="The ARN of the AgentCore Auditor agent"
        )

        writerAgentARN = CfnParameter(
            self,
            "writerAgentARN",
            type="String",
            description="The ARN of the AgentCore Writer agent"
        )

        KMS_SQS_KeyARN = Fn.import_value(f"{KnowledgeIngestionStackName.value_as_string}KMS-SQS-Key") 
        SQSQueueARN = Fn.import_value(f"{KnowledgeIngestionStackName.value_as_string}FargateQueue")
        DynamoDBTableARN = Fn.import_value(f"{KnowledgeIngestionStackName.value_as_string}AnalysisTable")
        S3BucketARN = Fn.import_value(f"{KnowledgeIngestionStackName.value_as_string}ReportsS3Bucket")

        #DynamoDB jobs table
        self.jobsTable = dynamodb.Table.from_table_arn(
            self,
            "ComplianceJobs-Table",
            table_arn=DynamoDBTableARN
        )

        #KMS key
        self.kmsKey = kms.Key.from_key_arn(
            self,
            "KMS-SQS-Key",
            key_arn=KMS_SQS_KeyARN
        )

        #SQS Queue
        self.sqsQueue = sqs.Queue.from_queue_arn(
            self,
            "SQSAnalysis-Queue",
            queue_arn=SQSQueueARN
        )

        #S3 Bucket
        self.reports_bucket = s3.Bucket.from_bucket_arn(
            self,
            "ReportsS3Bucket",
            bucket_arn=S3BucketARN
        )

        #Create MultiAgent Compliance Analysis
        multiagent_compliance_analysis = MultiAgentComplianceAnalysis(
            self,
            construct_id="MultiagentComplianceWorkflow",
            dynamod_db_jobs_table=self.jobsTable,
            sqs_fargate_queue=self.sqsQueue,
            kms_sqs_key=self.kmsKey,
            reports_s3_bucket=self.reports_bucket,
            lawyer_agent_arn=lawyerAgentARN.value_as_string,
            writer_agent_arn=writerAgentARN.value_as_string,
            auditor_agent_arn=auditorAgentARN.value_as_string
        )

        CfnOutput(
            self,
            "RegionName",
            value=self.region,
            export_name=f"{Stack.of(self).stack_name}RegionName",
        )

        # cdk-nag suppressions
        stack_suppressions = [
            # Insert your stack-level NagPackSuppression's here
        ]
        NagSuppressions.add_stack_suppressions(
            stack=self,
            suppressions=stack_suppressions,
        )
