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
    aws_lambda,
    Stack,
)
from constructs import Construct

from cdk_nag import NagSuppressions, NagPackSuppression


class PutQuestionSet(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        api: apigw.IRestApi,
        request_validator: apigw.IRequestValidator,
        resource_path: str,
        http_method: str,
        cognito_authorizer: apigw.IAuthorizer,
        lambda_function: aws_lambda.Function,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        compliance_report_question_set_model = api.add_model(
            "PutReportQuestionSetRequest",
            schema=apigw.JsonSchema(
                schema=apigw.JsonSchemaVersion.DRAFT4,
                title="PutReportQuestionSetRequest",
                type=apigw.JsonSchemaType.OBJECT,
                properties={
                    "job_id": apigw.JsonSchema(type=apigw.JsonSchemaType.STRING),
                    "question_set": apigw.JsonSchema(type=apigw.JsonSchemaType.OBJECT),
                },
                required=["job_id", "question_set"],
            ),
            content_type="application/json",
        )

        integrator = apigw.LambdaIntegration(lambda_function)

        path_parts = list(filter(bool, resource_path.split("/")))
        resource = api.root
        for path_part in path_parts:
            child_resource = resource.get_resource(path_part)
            if not child_resource:
                child_resource = resource.add_resource(path_part)
            resource = child_resource


        resource.add_method(
            http_method=http_method,
            integration=integrator,
            authorizer=cognito_authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
            request_validator=request_validator,
            request_models={"application/json": compliance_report_question_set_model},
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
        )