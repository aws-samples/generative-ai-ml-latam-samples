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
    Stack,
    aws_iam as iam,
    CfnOutput,
)
from constructs import Construct

from cdk_nag import NagSuppressions


class AgentCoreIAMStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the IAM role for Bedrock Agent Core
        agent_core_role = iam.Role(
            self,
            "AgentCoreRole",
            role_name="AgentCore-ExecutionRole",
            assumed_by=iam.ServicePrincipal(
                service="bedrock-agentcore.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "aws:SourceAccount": Stack.of(self).account
                    },
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:bedrock-agentcore:{Stack.of(self).region}:{Stack.of(self).account}:*"
                    }
                }
            ),
        )

        # ECR Image Access Policy
        ecr_image_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "ecr:BatchGetImage",
                "ecr:GetDownloadUrlForLayer"
            ],
            resources=[f"arn:aws:ecr:{Stack.of(self).region}:{Stack.of(self).account}:repository/*"]
        )

        # Logs Access Policy
        logs_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "logs:DescribeLogStreams",
                "logs:CreateLogGroup",
                "logs:DescribeLogGroups",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            resources=[
                f"arn:aws:logs:{Stack.of(self).region}:{Stack.of(self).account}:log-group:/aws/bedrock-agentcore/runtimes/*",
                f"arn:aws:logs:{Stack.of(self).region}:{Stack.of(self).account}:log-group:*",
                f"arn:aws:logs:{Stack.of(self).region}:{Stack.of(self).account}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
            ]
        )

        # ECR Token Access Policy
        ecr_token_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["ecr:GetAuthorizationToken"],
            resources=["*"]
        )

        # X-Ray Access Policy
        xray_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "xray:PutTraceSegments",
                "xray:PutTelemetryRecords",
                "xray:GetSamplingRules",
                "xray:GetSamplingTargets"
            ],
            resources=["*"]
        )

        # CloudWatch Access Policy
        cloudwatch_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["cloudwatch:PutMetricData"],
            resources=["*"],
            conditions={
                "StringEquals": {
                    "cloudwatch:namespace": "bedrock-agentcore"
                }
            }
        )

        # Get Agent Access Token Policy
        agent_token_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock-agentcore:GetWorkloadAccessToken",
                "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                "bedrock-agentcore:GetWorkloadAccessTokenForUserId"
            ],
            resources=[
                f"arn:aws:bedrock-agentcore:{Stack.of(self).region}:{Stack.of(self).account}:workload-identity-directory/default",
                f"arn:aws:bedrock-agentcore:{Stack.of(self).region}:{Stack.of(self).account}:workload-identity-directory/default/workload-identity/agentName-*"
            ]
        )

        # Bedrock Model Invocation Policy
        bedrock_model_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            resources=[
                "arn:aws:bedrock:*::foundation-model/*",
                f"arn:aws:bedrock:{Stack.of(self).region}:{Stack.of(self).account}:*"
            ]
        )

        # Parameter Store Access Policy
        parameter_store_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:GetParametersByPath"
            ],
            resources=[
                f"arn:aws:ssm:{Stack.of(self).region}:{Stack.of(self).account}:parameter/*"
            ]
        )

        # Add all policies to the role
        agent_core_role.add_to_policy(ecr_image_policy)
        agent_core_role.add_to_policy(logs_policy)
        agent_core_role.add_to_policy(ecr_token_policy)
        agent_core_role.add_to_policy(xray_policy)
        agent_core_role.add_to_policy(cloudwatch_policy)
        agent_core_role.add_to_policy(agent_token_policy)
        agent_core_role.add_to_policy(bedrock_model_policy)
        agent_core_role.add_to_policy(parameter_store_policy)

        NagSuppressions.add_resource_suppressions(
            agent_core_role,
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Service role for agent core. Use of * for prototyping. Recommend to change in P2P""",
                },
            ],
            True
        )

        # Output the role ARN
        CfnOutput(
            self,
            "AgentCoreRoleArn",
            value=agent_core_role.role_arn,
            export_name=f"{Stack.of(self).stack_name}AgentCoreExecutionRoleArn",
            description="ARN of the Agent Core IAM Role"
        )