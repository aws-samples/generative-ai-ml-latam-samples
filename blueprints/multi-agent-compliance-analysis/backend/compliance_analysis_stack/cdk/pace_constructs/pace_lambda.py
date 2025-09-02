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
    aws_lambda_python_alpha as lambda_python,
    aws_lambda as lambda_,
    aws_iam as iam,
    Stack
)
from constructs import Construct
from cdk_nag import NagSuppressions, NagPackSuppression


class PACEPythonFunction(lambda_python.PythonFunction):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            **kwargs,
    ):
        role = iam.Role(
            scope,
            f"{construct_id}ServiceRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        super().__init__(
            scope,
            construct_id,
            role=role,
            **kwargs,
        )

        function_name = self.function_name
        role.attach_inline_policy(_lambda_basic_policy(scope, construct_id, function_name))
        role.attach_inline_policy(_lambda_vpc_policy(scope, construct_id))


class PACEDockerImageFunction(lambda_.DockerImageFunction):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            **kwargs,
    ):
        role = iam.Role(
            scope,
            f"{construct_id}ServiceRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        super().__init__(
            scope,
            construct_id,
            role=role,
            **kwargs,
        )

        function_name = self.function_name
        role.attach_inline_policy(_lambda_basic_policy(scope, construct_id, function_name))
        role.attach_inline_policy(_lambda_vpc_policy(scope, construct_id))


def _lambda_basic_policy(
        scope: Construct,
        construct_id: str,
        function_name: str
):
    region = Stack.of(scope).region
    account = Stack.of(scope).account

    policy = iam.Policy(
        scope,
        f"{construct_id}LambdaBasicExecPolicy",
        statements=[
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    f"arn:aws:logs:{region}:{account}:log-group:/aws/lambda/{function_name}",
                    f"arn:aws:logs:{region}:{account}:log-group:/aws/lambda/{function_name}:*"
                ],
            ),
        ],
    )
    NagSuppressions.add_resource_suppressions(
        construct=policy,
        suppressions=[NagPackSuppression(id="AwsSolutions-IAM5", reason="AWSLambdaBasicExecutionRole")],
    )
    return policy


def _lambda_vpc_policy(
        scope: Construct,
        construct_id: str,
):
    policy = iam.Policy(
        scope,
        f"{construct_id}LambdaVPCExecPolicy",
        statements=[
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ec2:CreateNetworkInterface",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:DeleteNetworkInterface",
                    "ec2:AssignPrivateIpAddresses",
                    "ec2:UnassignPrivateIpAddresses",
                ],
                resources=["*"],
            ),
        ],
    )
    NagSuppressions.add_resource_suppressions(
        construct=policy,
        suppressions=[NagPackSuppression(id="AwsSolutions-IAM5", reason="AWSLambdaVPCAccessExecutionRole")],
    )
    return policy
