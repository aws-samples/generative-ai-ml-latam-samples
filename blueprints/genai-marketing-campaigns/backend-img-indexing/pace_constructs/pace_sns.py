# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_sns as sns,
    aws_kms as kms,
    aws_iam as iam,
)
from constructs import Construct


class PACETopic(sns.Topic):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            **kwargs,
    ):
        self.master_key = kms.Alias.from_alias_name(scope, f"{construct_id}MasterKey", "alias/aws/sns")
        super().__init__(
            scope,
            construct_id,
            master_key=self.master_key,
            **kwargs
        )
        sns.TopicPolicy(
            scope,
            f"{construct_id}TopicPolicy",
            topics=[self],
            policy_document=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        sid="AllowPublishThroughSSLOnly",
                        actions=["SNS:Publish"],
                        effect=iam.Effect.DENY,
                        resources=[self.topic_arn],
                        conditions={
                            "Bool": {
                                "aws:SecureTransport": "false",
                            },
                        },
                        principals=[iam.AnyPrincipal()],
                    ),
                ],
            ),
        )
