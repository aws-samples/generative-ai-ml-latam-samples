# Copyright 2025 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: LicenseRef-.amazon.com.-AmznSL-1.0
# Licensed under the Amazon Software License  http://aws.amazon.com/asl/

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
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda_python_alpha as lambda_python,
    aws_lambda as lambda_,
    aws_sqs as sqs,
    aws_kms as kms,
    aws_ssm as ssm
)

from constructs import Construct
from cdk_nag import NagSuppressions

from workflows.document_indexing import DocumentIndexingStack
from workflows.document_question_generation import DocumentQuestionGenerationStack
from workflows.compliance_report_workflow import ComplianceReportStack
from api.indexDocument import IndexDocumentAPI
from api.generateQuestions import GenerateQuestionsAPI
from api.complianceReports import ComplianceReportsAPI


import pace_constructs as pace

APP_DIR = os.path.join(os.path.dirname(__file__), "..", "app")


class BackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        pages_chunk = CfnParameter(
            self,
            "PagesChunk",
            type="String",
            description="The number of pages per chunk",
            default="5"
        )

        max_questions_per_chunk = CfnParameter(
            self,
            "QuestionsChunk",
            type="String",
            description="The maximum number of questions per chunk",
            default="20"
        )

        regulation_pages_chunk = CfnParameter(
            self,
            "RegulationPagesChunk",
            type="String",
            description="The number of pages per chunk for the regulation documents",
            default="30"
        )

        regulation_max_questions_per_chunk = CfnParameter(
            self,
            "RegulationQuestionsChunk",
            type="String",
            description="The maximum number of questions per chunk for the regulation documents",
            default="20"
        )

        agentCoreIAMRoleARN = CfnParameter(
            self,
            "IAMAgentCoreExecutionRoleARN",
            type="String",
            description="The ARN of the IAM role assumed by AgentCore"
        )

        # API resources
        self.cognito = pace.PACECognito(
            self,
            "Cognito",
            region=self.region,
        )

        # IAM role to read and write from the vector collection
        self.vectorCollectionRole = iam.Role(self, "VectorCollectionRole", assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"))

        # OpenSearch Serverless Vector Collection
        self.vectorCollection = opensearchserverless.VectorCollection(
            self,
            "VectorCollection",
            collection_name="meta-kb-vector-collection",
            collection_type=opensearchserverless.VectorCollectionType.VECTORSEARCH
        )
        self.vectorCollection.grant_data_access(self.vectorCollectionRole)

        self.vectorIndex = opensearch_vectorindex.VectorIndex(
            self,
            "VectorIndex",
            vector_dimensions=1024,
            collection=self.vectorCollection,
            index_name='meta-kb-index',
            vector_field='embedding',
            mappings=[
                opensearch_vectorindex.MetadataManagementFieldProps(
                    mapping_field='persona',
                    data_type='keyword',
                    filterable=True
                ),
                opensearch_vectorindex.MetadataManagementFieldProps(
                    mapping_field='perspective',
                    data_type='keyword',
                    filterable=True
                ),
                opensearch_vectorindex.MetadataManagementFieldProps(
                    mapping_field='doc_key',
                    data_type='text',
                    filterable=False
                ),
                opensearch_vectorindex.MetadataManagementFieldProps(
                    mapping_field='doc_version',
                    data_type='text',
                    filterable=False
                ),
                opensearch_vectorindex.MetadataManagementFieldProps(
                    mapping_field='question',
                    data_type='text',
                    filterable=False
                ),
                opensearch_vectorindex.MetadataManagementFieldProps(
                    mapping_field='answer',
                    data_type='text',
                    filterable=False
                )
            ],
            analyzer=opensearch_vectorindex.Analyzer(
                character_filters=[
                    opensearchserverless.CharacterFilterType.ICU_NORMALIZER
                ],
                tokenizer=opensearchserverless.TokenizerType.KUROMOJI_TOKENIZER,
                token_filters=[
                    opensearchserverless.TokenFilterType.KUROMOJI_BASEFORM,
                    opensearchserverless.TokenFilterType.JA_STOP,
                ],
            )
        )
        NagSuppressions.add_resource_suppressions_by_path(
            self,
            '/dataIngestionBackend/LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/ServiceRole/Resource',
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Policy created by GenAI CDK Constructs to create role to access the OpenSearch Serverless Index""",
                    "appliesTo": [
                        "Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
                    ],
                },
            ],
            True,
        )
        NagSuppressions.add_resource_suppressions_by_path(
            self,
            '/dataIngestionBackend/LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/ServiceRole/DefaultPolicy/Resource',
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Policy created by GenAI CDK Constructs to create role to access the OpenSearch Serverless Index""",
                },
            ],
            True,
        )

        kb_opensearch_host_ssm_param = ssm.StringParameter(
            self,
            "KBOpenSearchServerlessHost",
            parameter_name=f"/{Stack.of(self).stack_name}/knowledge_base/opensearch-serverless-host",
            string_value=self.vectorCollection.collection_endpoint,
            description="Endpoint of the host of the OpenSearch Serverless collection for the knowledge base"
        )

        kb_opensearch_port_ssm_param = ssm.StringParameter(
            self,
            "KBOpenSearchServerlessPort",
            parameter_name=f"/{Stack.of(self).stack_name}/knowledge_base/opensearch-serverless-port",
            string_value="443",
            description="Port of the hots of the OpenSearch Serverless collection for the knowledge base"
        )

        kb_opensearch_index_ssm_param = ssm.StringParameter(
            self,
            "KBOpenSearchServerlessIndex",
            parameter_name=f"/{Stack.of(self).stack_name}/knowledge_base/opensearch-serverless-index",
            string_value=self.vectorIndex.index_name,
            description="Index of the knowledge base vector collection"
        )

        self.jobsTable = pace.PACETable(
            self,
            "ComplianceJobs-Table",
            partition_key=dynamodb.Attribute(name="job_id", type=dynamodb.AttributeType.STRING),
        )

        # Shared Lambda layer with Python packaging for main job steps status
        self.shared_utils_layer = lambda_python.PythonLayerVersion(
            self,
            "ComplianceReportsSharedUtilsLayer",
            entry=os.path.join(APP_DIR, "../../", "shared"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_13],
        )

        # KMS keys for this app
        self.sqs_kms_key = kms.Key(self,
                                   "ComplianceAnalysis-SQS-KMSKey",
                                   alias=f"compliance-sqs-key-{Stack.of(self).stack_name}",
                                   enable_key_rotation=True
                                   )

        # An SQS Queue to receive events
        self.analysis_sqs_queue = sqs.Queue(
            self,
            "ComplianceAnalysisEventsSQSQueue",
            visibility_timeout=Duration.seconds(60 * 5),
            retention_period=Duration.minutes(1),
            queue_name="ComplianceAnalysisEventsSQSQueue",
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=self.sqs_kms_key,
            enforce_ssl=True
        )

        # A dead letter SQS queue for the main SQS queue
        self.analysis_sqs_dead_letter_queue = sqs.Queue(
            self,
            "ComplianceAnalysisEventsSQSQueueDeadLetterQueue",
            visibility_timeout=Duration.seconds(60 * 5),
            queue_name="ComplianceAnalysisEventsSQSQueueDeadLetterQueue",
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=self.sqs_kms_key,
            enforce_ssl=True,
            retention_period=Duration.days(14),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=self.analysis_sqs_queue,
            ),
        )

        # A S3 bucket to store the documents
        self.reports_bucket = pace.PACEBucket(
            self,
            "ComplianceReportsBucket"
        )

        #Document indexing workflow
        document_indexing_workflow = DocumentIndexingStack(
            self,
            "DocumentIndexingWorkflow",
            pages_per_chunk=pages_chunk.value_as_string,
            questions_per_chunk=max_questions_per_chunk.value_as_string,
            language_code="en",
            #metadata_table=self.summariesTable,
            oss_data_indexing_role=self.vectorCollectionRole,
            oss_host=self.vectorCollection.collection_endpoint,
            oss_index_name=self.vectorIndex.index_name,
            shared_utils_layer=self.shared_utils_layer
        )

        kb_summaries_table_ssm_param = ssm.StringParameter(
            self,
            "KBDynamoDBTableName",
            parameter_name=f"/{Stack.of(self).stack_name}/knowledge_base/dynamodb-metakb-summary-table-name",
            string_value=document_indexing_workflow.summaries_table.table_name,
            description="Table name of the knowledge base summaries"
        )

        #Questions for document workflow
        regulation_docs_processing_workflow = DocumentQuestionGenerationStack(
            self,
            "QuestionForRegulationWorkflow",
            pages_per_chunk=regulation_pages_chunk.value_as_string,
            questions_per_chunk=regulation_max_questions_per_chunk.value_as_string,
            language_code="en",
            main_jobs_table=self.jobsTable,
            shared_utils_layer=self.shared_utils_layer
        )

        #Compliance Report Workflow
        compliance_report_generation = ComplianceReportStack(
            self,
            "ComplianceReportGeneration",
            language_code="en",
            reports_bucket=self.reports_bucket,
            compliance_analysis_jobs_table=self.jobsTable,
            question_jobs_table=regulation_docs_processing_workflow.jobs_table,
            shared_utils_layer=self.shared_utils_layer
        )

        #Document indexing API
        IndexDocumentAPI(
            self,
            "IndexDocumentAPI",
            document_bucket=document_indexing_workflow.docs_bucket,
            jobs_table=document_indexing_workflow.jobs_table,
            sns_textract_topic=document_indexing_workflow.sns_topic,
            sns_textract_role=document_indexing_workflow.textract_sns_role,
            shared_utils_layer=self.shared_utils_layer,
            cognitoUserPool=self.cognito.user_pool
        )

        #Question Generation API
        GenerateQuestionsAPI(
            self,
            "QuestionGeneratorAPI",
            document_bucket=regulation_docs_processing_workflow.docs_bucket,
            jobs_table=regulation_docs_processing_workflow.jobs_table,
            sns_textract_topic=regulation_docs_processing_workflow.sns_topic,
            sns_textract_role=regulation_docs_processing_workflow.textract_sns_role,
            shared_utils_layer=self.shared_utils_layer,
            main_jobs_table=self.jobsTable,
            cognitoUserPool=self.cognito.user_pool
        )

        #Compliance Report Management API
        ComplianceReportsAPI(
            self,
            "ComplianceReportsAPI",
            document_bucket=self.reports_bucket,
            compliance_analysis_jobs_table=self.jobsTable,
            start_analysis_sqs_queue=self.analysis_sqs_queue,
            report_layout_workflow_machine=compliance_report_generation.compliance_report_pipeline_sfn,
            shared_utils_layer=self.shared_utils_layer,
            cognitoUserPool=self.cognito.user_pool
        )

        # AgentCore execution role
        self.agentCoreExecutionRole = iam.Role.from_role_arn(self, "AgentCoreExecutionRole", agentCoreIAMRoleARN.value_as_string)

        self.agentCoreExecutionRole.attach_inline_policy(
            iam.Policy(
                self,
                "AmazonOpenSearchServerlessAccess",
                document=iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "aoss:APIAccessAll",
                                "aoss:DashboardsAccessAll"
                            ],
                            resources=[
                                self.vectorCollection.collection_arn,
                                f"arn:aws:aoss:{Stack.of(self).region}:{Stack.of(self).account}:dashboards/default"
                            ]
                        )
                    ]
                )
            )
        )

        self.vectorCollection.grant_data_access(self.agentCoreExecutionRole)
        document_indexing_workflow.summaries_table.grant_read_data(self.agentCoreExecutionRole)

        NagSuppressions.add_resource_suppressions(
            self.agentCoreExecutionRole,
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for agent core. Use of * for prototyping. Recommend to change in P2P""",
                },
            ],
            True
        )

        CfnOutput(
            self,
            "RegionName",
            value=self.region,
            export_name=f"{Stack.of(self).stack_name}RegionName",
        )

        CfnOutput(
            self,
            "DynamoDBAnalysisTable",
            value=self.jobsTable.table_arn,
            export_name=f"{Stack.of(self).stack_name}AnalysisTable",
        )

        CfnOutput(
            self,
            "DynamoDBMetaKBTable",
            value=document_indexing_workflow.summaries_table.table_name,
            export_name=f"{Stack.of(self).stack_name}MetaKBTableName",
        )

        CfnOutput(
            self,
            "SQSFargateQueue",
            value=self.analysis_sqs_queue.queue_arn,
            export_name=f"{Stack.of(self).stack_name}FargateQueue",
        )

        CfnOutput(
            self,
            "KMS-SQS-Key",
            value=self.sqs_kms_key.key_arn,
            export_name=f"{Stack.of(self).stack_name}KMS-SQS-Key",
        )

        CfnOutput(
            self,
            "ReportsS3Bucket",
            value=self.reports_bucket.bucket_arn,
            export_name=f"{Stack.of(self).stack_name}ReportsS3Bucket",
        )

        CfnOutput(
            self,
            "VectorCollectionEndpoint",
            value=self.vectorCollection.collection_endpoint,
            export_name=f"{Stack.of(self).stack_name}VectorCollectionEndpoint",
        )

        CfnOutput(
            self,
            "VectorIndexName",
            value=self.vectorIndex.index_name,
            export_name=f"{Stack.of(self).stack_name}VectorIndexName",
        )

        # cdk-nag suppressions
        stack_suppressions = [
            # Insert your stack-level NagPackSuppression's here
        ]
        NagSuppressions.add_stack_suppressions(
            stack=self,
            suppressions=stack_suppressions,
        )
