# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os

from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_lambda_python_alpha as lambda_python,
    aws_lambda as lambda_,
    aws_opensearchserverless as opensearch_serverless,
    custom_resources as cr,
    aws_logs as logs,
    CustomResource,
    CfnOutput,
    Names,
    Duration,
    CfnParameter,
)

from constructs import Construct

from cdk_nag import NagSuppressions

class OpenSearchServerlessEmbeddingsIndex(Construct):
    """A Construct to create an OpenSearch Serverless instance."""

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            oss_collection_name: CfnParameter,
            oss_embeddings_index_name: CfnParameter,
            oss_data_indexing_role: iam.Role,
            oss_data_query_role: iam.Role,
    ) -> None:
        super().__init__(scope, construct_id)

        # Create an IAM role to access the data in open search

        oss_data_access_policy = opensearch_serverless.CfnAccessPolicy(
            self,
            "EmbeddingsDataAccessPolicy",
            name="embed-acc-pol",
            policy='[{"Description":"Access for acceess role","Rules":[{"ResourceType":"index","Resource":["index/*/*"],"Permission":["aoss:*"]},{"ResourceType":"collection","Resource":["collection/' + \
                   oss_collection_name.value_as_string + '"],"Permission":["aoss:*"]}],"Principal":["' + \
                   oss_data_indexing_role.role_arn + '", "' + oss_data_query_role.role_arn + '"]}]',
            type="data",
            description="Data access policy for embeddings collection"
        )

        oss_network_policy = opensearch_serverless.CfnSecurityPolicy(
            self,
            "EmbeddingsNetworkPolicy",
            name="embed-net-pol",
            policy='[{"Rules":[{"ResourceType":"collection","Resource":["collection/' + \
                   oss_collection_name.value_as_string + '"]}, {"ResourceType":"dashboard","Resource":["collection/' + \
                   oss_collection_name.value_as_string + '"]}],"AllowFromPublic":true}]',
            type="network",
            description="Network policy for embeddings collection"
        )

        oss_encryption_policy = opensearch_serverless.CfnSecurityPolicy(
            self,
            "EmbeddingsEncryptionPolicy",
            name="embed-encry-pol",
            policy='{"Rules":[{"ResourceType":"collection","Resource":["collection/' + oss_collection_name.value_as_string + '"]}],"AWSOwnedKey":true}',
            type="encryption",
            description="Encryption policy for embeddings collection"
        )

        # Create an open search serverless collection
        self.oss_embeddings_collection = opensearch_serverless.CfnCollection(
            self,
            "EmbeddingsCollection",
            name=oss_collection_name.value_as_string,
            description="Collection to store generated image and text embeddings",
            standby_replicas="DISABLED",
            type="VECTORSEARCH",
        )
        self.oss_embeddings_collection.add_dependency(oss_data_access_policy)
        self.oss_embeddings_collection.add_dependency(oss_network_policy)
        self.oss_embeddings_collection.add_dependency(oss_encryption_policy)

        # Add permissions to IAM role to access the collection
        oss_data_indexing_role.add_to_principal_policy(
            iam.PolicyStatement(
                actions=["aoss:APIAccessAll"],
                resources=[self.oss_embeddings_collection.attr_arn],
                effect=iam.Effect.ALLOW,
            )
        )
        oss_data_indexing_role.add_to_principal_policy(
            iam.PolicyStatement(
                actions=["aoss:DashboardsAccessAll"],
                resources=[f'arn:aws:aoss:us-east-1:{Stack.of(self).account}:dashboards/default'],
                effect=iam.Effect.ALLOW,
            )
        )

        # Create OpenSearch Vector Index for storing the image embeddings
        create_open_search_index_fn = lambda_python.PythonFunction(
            self,
            "CreateOpenSearchIndexFn",
            entry=os.path.join(
                os.path.dirname(__file__), "custom_resources", "create_oss_embeddings_index"
            ),
            index="create_oss_embeddings_index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(60),
            memory_size=128,
            environment={
                "LOG_LEVEL": "DEBUG",
            },
            role=oss_data_indexing_role
        )

        create_open_search_index_provider = cr.Provider(
            self,
            "CreateOpenSearchIndexProvider",
            on_event_handler=create_open_search_index_fn,
            log_retention=logs.RetentionDays.ONE_DAY,  # default is INFINITE
        )
        NagSuppressions.add_resource_suppressions(
            create_open_search_index_provider,
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Policy implemented by CDK""",
                },
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": """Managed policy implemented by CDK""",
                    "appliesTo": [
                        "Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
                    ],
                },
                {
                    "id": "AwsSolutions-L1",
                    "reason": """Policy managed by AWS can not specify a different runtime version""",
                },
            ],
            True,
        )

        self.create_open_search_index_custom_resource = CustomResource(
            self,
            "CreateOpenSearchIndexCustomResource",
            service_token=create_open_search_index_provider.service_token,
            properties={
                "IndexName": oss_embeddings_index_name.value_as_string,
                "Endpoint": self.oss_embeddings_collection.attr_collection_endpoint,
                "Region": Stack.of(self).region,
            },
        )

        # Outputs
        CfnOutput(
            self,
            "DashboardURL",
            value=self.oss_embeddings_collection.attr_dashboard_endpoint,
            export_name=f"{Stack.of(self).stack_name}OSSDashboardURL",
        )

        CfnOutput(
            self,
            "CollectionURL",
            value=self.oss_embeddings_collection.attr_collection_endpoint,
            export_name=f"{Stack.of(self).stack_name}OSSCollectionURL",
        )

        CfnOutput(
            self,
            "CollectionARN",
            value=self.oss_embeddings_collection.attr_arn,
            export_name=f"{Stack.of(self).stack_name}OSSCollectionARN",
        )
