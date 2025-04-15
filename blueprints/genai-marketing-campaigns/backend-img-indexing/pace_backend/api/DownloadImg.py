# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_s3 as s3,
    Stack,
)
from constructs import Construct

from cdk_nag import NagSuppressions, NagPackSuppression

import pace_constructs as pace

class DownloadImg(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        api_gw: pace.PACEApiGateway,
        api_role: iam.IRole,
        imgs_bucket: s3.IBucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        imgs_bucket.grant_read_write(api_role)

        download_img_integration = apigw.AwsIntegration(
            service="s3",
            region=Stack.of(self).region,
            integration_http_method="GET",
            path=f"{imgs_bucket.bucket_name}" + "/{folder}/{imageFile}",
            options=apigw.IntegrationOptions(
                credentials_role=api_role,
                request_parameters={
                    "integration.request.path.folder": "method.request.path.folder",
                    "integration.request.path.imageFile": "method.request.path.imageFile",
                    "integration.request.header.Accept": "method.request.header.Accept",
                },
                integration_responses=[
                    apigw.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Content-Type": "integration.response.header.Content-Type"
                        },
                    )
                ],
            ),
        )

        child_resource = api_gw.rest_api.root.get_resource("imgMetaIndex")
        if not child_resource:
            child_resource = api_gw.rest_api.add_resource("imgMetaIndex")
        resource = child_resource

        download_img = (
            resource
            .add_resource("download")
            .add_resource("{folder}")
            .add_resource("{imageFile}")
        )

        download_img_method = download_img.add_method(
            "GET",
            download_img_integration,
            authorizer=api_gw.cognito_authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
            request_parameters={
                "method.request.header.Accept": True,
                "method.request.header.Content-Type": True,
                "method.request.path.folder": True,
                "method.request.path.imageFile": True,
            },
            method_responses=[
                {
                    "statusCode": "200",
                    "responseParameters": {"method.response.header.Content-Type": True},
                }
            ],
            request_models={
                "image/jpeg": api_gw.jpeg_model,
                "image/png": api_gw.png_model,
            },
            request_validator=api_gw.request_body_params_validator,
        )

        for method in api_gw.rest_api.methods:
            resource = method.node.find_child("Resource")
            if method.http_method == "OPTIONS":
                NagSuppressions.add_resource_suppressions(
                    construct=resource,
                    suppressions=[
                        NagPackSuppression(
                            id="AwsSolutions-COG4",
                            reason="OPTIONS method for CORS pre-flight should not use authorization",
                        ),
                        NagPackSuppression(
                            id="AwsSolutions-APIG4",
                            reason="OPTIONS method for CORS pre-flight should not use authorization",
                        ),
                    ],
                )