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
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_s3 as s3,
    Stack,
)
from constructs import Construct

import pace_constructs as pace

from cdk_nag import NagSuppressions, NagPackSuppression

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
        NagSuppressions.add_resource_suppressions(
            api_role,
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Policy implemented by CDK when using S3 grant read/write""",
                },
            ],
            True,
        )

        jpeg_model = api_gw.rest_api.add_model(
            "JPEGImage",
            schema=apigw.JsonSchema(),
            content_type="image/jpeg",
        )
        png_model = api_gw.rest_api.add_model(
            "PngImage",
            schema=apigw.JsonSchema(),
            content_type="image/png",
        )

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

        download_img = (
            api_gw.rest_api.root
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
                "image/jpeg": jpeg_model,
                "image/png": png_model,
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