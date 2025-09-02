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
    aws_stepfunctions as sfn,
    Stack,
)
from constructs import Construct

from cdk_nag import NagSuppressions, NagPackSuppression

create_report_layout_request_template = """{\\"job_id\\":\\"$inputRoot.job_id\\",
                        \\"report_template\\":$util.escapeJavaScript($input.json('$.report_template'))
                    }""".replace('\n', '').replace(" ", "").strip()


class CreateReportLayout(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        api: apigw.IRestApi,
        request_validator: apigw.IRequestValidator,
        api_role: iam.IRole,
        resource_path: str,
        cognito_authorizer: apigw.IAuthorizer,
        workflow_machine: sfn.IStateMachine,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        workflow_machine.grant_start_execution(api_role)

        compliance_report_layout_request_model = api.add_model(
            "CreateReportLayoutRequest",
            schema=apigw.JsonSchema(
                schema=apigw.JsonSchemaVersion.DRAFT4,
                title="CreateReportLayoutRequest",
                type=apigw.JsonSchemaType.OBJECT,
                properties={
                    "job_id": apigw.JsonSchema(type=apigw.JsonSchemaType.STRING),
                    "report_template": apigw.JsonSchema(type=apigw.JsonSchemaType.OBJECT),
                },
                required=["job_id", "report_template"],
            ),
            content_type="application/json",
        )

        create_report_layout_integration = apigw.AwsIntegration(
            service="states",
            region=Stack.of(self).region,
            action="StartExecution",
            integration_http_method="POST",
            options=apigw.IntegrationOptions(
                credentials_role=api_role,
                request_templates=
                {
                    "application/json": f"""
                    #set($inputRoot = $input.path('$'))
                    {{
                        "stateMachineArn": "{workflow_machine.state_machine_arn}",
                        "input": "{create_report_layout_request_template}"
                    }}"""
                },
                integration_responses=[
                    apigw.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": "'*'"
                        }
                    )
                ],
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
            "POST",
            integration=create_report_layout_integration,
            authorizer=cognito_authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
            request_models={
                "application/json": compliance_report_layout_request_model,
            },
            request_validator=request_validator,
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