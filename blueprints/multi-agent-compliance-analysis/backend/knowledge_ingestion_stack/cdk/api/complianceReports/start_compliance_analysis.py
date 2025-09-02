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
    Stack,
    aws_apigateway as apigw,
    aws_lambda,
    aws_apigateway as apigateway,
    aws_sqs as sqs,
    aws_iam as iam,
)
from constructs import Construct
from cdk_nag import NagSuppressions, NagPackSuppression

class StartComplianceAnalysis(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        api: apigw.IRestApi,
        request_validator: apigw.IRequestValidator,
        resource_path: str,
        cognito_authorizer: apigw.IAuthorizer,
        api_role: iam.Role,
        sqs_queue: sqs.Queue,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #Grant access for APi role to send messages to sqs
        sqs_queue.grant_send_messages(api_role)

        NagSuppressions.add_resource_suppressions(
            api_role,
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Policies added an managed by AWS CDK. Policiy needed for sending sqs messages via API""",
                },
            ],
            True
        )

        compliance_report_request_model = api.add_model(
            "ComplianceAnalysisRequest",
            schema=apigw.JsonSchema(
                schema=apigw.JsonSchemaVersion.DRAFT4,
                title="ComplianceAnalysisRequest",
                type=apigw.JsonSchemaType.OBJECT,
                properties={
                    "job_id": apigw.JsonSchema(type=apigw.JsonSchemaType.STRING),
                }
            ),
            content_type="application/json",
        )

        apigw_sqs_integration = apigateway.AwsIntegration(
            service="sqs",
            path=f"{Stack.of(self).account}/{sqs_queue.queue_name}",
            integration_http_method="POST",
            options=apigateway.IntegrationOptions(
                credentials_role=api_role,
                request_parameters={
                    "integration.request.header.Content-Type": "'application/x-amz-json-1.0'",
                    "integration.request.querystring.Action": "'SendMessage'",
                    "integration.request.querystring.MessageBody": "method.request.body"
                },
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": "'*'"
                        },
                        response_templates={
                            "application/json": '{"message": "Message sent to queue"}'
                        }
                    )
                ]
            )
        )

        path_parts = list(filter(bool, resource_path.split("/")))
        resource = api.root
        for path_part in path_parts:
            child_resource = resource.get_resource(path_part)
            if not child_resource:
                child_resource = resource.add_resource(path_part)
            resource = child_resource

        resource.add_method(
            "POST",
            integration=apigw_sqs_integration,
            authorizer=cognito_authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                )
            ],
            request_models={
                "application/json": compliance_report_request_model,
            },
            request_validator=request_validator,
        )

        for method in api.methods:
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
