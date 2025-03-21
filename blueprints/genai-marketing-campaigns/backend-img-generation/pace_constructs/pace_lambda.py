# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_lambda_python_alpha as lambda_python,
    aws_lambda as lambda_,
    aws_iam as iam,
)
from constructs import Construct


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
        role.attach_inline_policy(_lambda_basic_policy(scope, construct_id))
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
        role.attach_inline_policy(_lambda_basic_policy(scope, construct_id))
        role.attach_inline_policy(_lambda_vpc_policy(scope, construct_id))


def _lambda_basic_policy(
        scope: Construct,
        construct_id: str,
):
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
                resources=["*"],
            ),
        ],
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

    return policy
