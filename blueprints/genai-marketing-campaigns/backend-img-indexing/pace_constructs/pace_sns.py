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
