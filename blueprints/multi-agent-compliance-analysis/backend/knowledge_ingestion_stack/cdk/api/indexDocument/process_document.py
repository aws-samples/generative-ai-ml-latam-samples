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

import typing
from aws_cdk import (
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_stepfunctions as sfn,
    aws_s3 as s3,
    aws_lambda,
    Stack,
)
from constructs import Construct

from cdk_nag import NagSuppressions, NagPackSuppression

class ProcessDocument(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        api: apigw.IRestApi,
        cognito_authorizer: apigw.IAuthorizer,
        resource_path: str,
        http_method: str,
        lambda_function: aws_lambda.Function,
        request_validator: apigw.RequestValidator,
        request_parameters: typing.Optional[typing.Mapping[str, bool]] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        process_document_request_model = api.add_model(
            "ProcessDocumentRequestModel",
            content_type="application/json",
            schema=apigw.JsonSchema(
                schema=apigw.JsonSchemaVersion.DRAFT4,
                title="ProcesDocumentSchema",
                type=apigw.JsonSchemaType.OBJECT,
                properties={
                    "key": apigw.JsonSchema(type=apigw.JsonSchemaType.STRING),
                    "metadata": apigw.JsonSchema(
                        type=apigw.JsonSchemaType.OBJECT,
                        properties={
                            "filename":  apigw.JsonSchema(type=apigw.JsonSchemaType.STRING),
                            "doc_key": apigw.JsonSchema(type=apigw.JsonSchemaType.STRING)
                        },
                        required=["filename", "doc_key"]
                    ),
                },
                required=["key", "metadata"],
            ),
        )

        path_parts = list(filter(bool, resource_path.split("/")))
        resource = api.root
        for path_part in path_parts:
            child_resource = resource.get_resource(path_part)
            if not child_resource:
                child_resource = resource.add_resource(path_part)
            resource = child_resource

        resource.add_method(
            http_method=http_method,
            integration=apigw.LambdaIntegration(lambda_function),
            authorizer=cognito_authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
            request_parameters=request_parameters,
            request_models={"application/json": process_document_request_model},
            request_validator=request_validator,
        )

        # Add Cognito auth to all methods except OPTIONS to allow for CORS header lookups
        for method in api.methods:
            resource = method.node.find_child("Resource")
            if method.http_method == "OPTIONS":
                resource.add_property_override("AuthorizationType", apigw.AuthorizationType.NONE)
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
            else:
                resource.add_property_override("AuthorizationType", apigw.AuthorizationType.COGNITO)
                resource.add_property_override("AuthorizerId", cognito_authorizer.authorizer_id)


