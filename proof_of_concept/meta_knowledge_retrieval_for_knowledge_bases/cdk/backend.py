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
    CfnOutput,
    RemovalPolicy,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
)

from constructs import Construct
from cdk_nag import NagSuppressions

APP_DIR = os.path.join(os.path.dirname(__file__))


class BackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.summaries_table = dynamodb.Table(
            self,
            "Meta-Knowledge-SummariesTable",
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            partition_key=dynamodb.Attribute(name="summary_key", type=dynamodb.AttributeType.STRING),
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
            '/MetaKnowledgeRetrieval/LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/ServiceRole/Resource',
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
            '/MetaKnowledgeRetrieval/LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/ServiceRole/DefaultPolicy/Resource',
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Policy created by GenAI CDK Constructs to create role to access the OpenSearch Serverless Index""",
                },
            ],
            True,
        )

        CfnOutput(
            self,
            "RegionName",
            value=self.region,
            export_name=f"{Stack.of(self).stack_name}RegionName",
        )

        CfnOutput(
            self,
            "DynamoDBMetaKBTable",
            value=self.summaries_table.table_name,
            export_name=f"{Stack.of(self).stack_name}MetaKBTableName",
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
