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
    aws_lambda,
    aws_apigateway as apigateway,
)
from constructs import Construct
from cdk_nag import NagSuppressions, NagPackSuppression


class CreateEmptyReport(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        api: apigw.IRestApi,
        resource_path: str,
        http_method: str,
        request_validator: apigw.IRequestValidator,
        cognito_authorizer: apigw.IAuthorizer,
        lambda_function: aws_lambda.Function,
        request_parameters: typing.Optional[typing.Mapping[str, bool]] = None,
    ) -> None:
        super().__init__(scope, id)

        create_compliance_job_request_model = api.add_model(
            "ComplianceAnalysisCreateEmptyReportRequestModel",
            content_type="application/json",
            schema=apigw.JsonSchema(
                schema=apigw.JsonSchemaVersion.DRAFT4,
                title="ComplianceAnalysisSchema",
                type=apigw.JsonSchemaType.OBJECT,
                properties={
                    "analysis_job_id": apigw.JsonSchema(type=apigw.JsonSchemaType.STRING),
                    "report_template": apigw.JsonSchema(type=apigw.JsonSchemaType.OBJECT)
                },
                required=["analysis_job_id", "report_template"],
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
            request_models={"application/json": create_compliance_job_request_model},
            request_validator=request_validator,
        )