# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0


from aws_cdk import (
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_stepfunctions as sfn,
    Stack,
)
from constructs import Construct


class GenerateMetaPrompt(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        api: apigw.IRestApi,
        validator: apigw.IRequestValidator,
        api_role: iam.IRole,
        authorizer: apigw.IAuthorizer,
        workflow_machine: sfn.IStateMachine,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        workflow_machine.grant_start_execution(api_role)

        img_suggest_request_model = api.add_model(
            "GenearateMetaPromptRequest",
            schema=apigw.JsonSchema(
                schema=apigw.JsonSchemaVersion.DRAFT4,
                title="GenearateMetaPromptRequest",
                type=apigw.JsonSchemaType.OBJECT,
            ),
            content_type="application/json",
        )

        img_suggest_integration = apigw.AwsIntegration(
            service="states",
            region=Stack.of(self).region,
            action="StartExecution",
            integration_http_method="POST",
            options=apigw.IntegrationOptions(
                credentials_role=api_role,
                request_templates=
                {
                    "application/json": f"""
                    #set($inputParams = $input.params())
                    #set($inputPath = $inputParams.path)
                    {{
                        "stateMachineArn": "{workflow_machine.state_machine_arn}",
                        "input": "{{
                        \\"httpMethod\\": \\"$context.httpMethod\\",
                        \\"path\\": \\"$context.path\\",
                        \\"id\\": \\"$inputPath.id\\",
                        \\"body\\": $util.escapeJavaScript($input.json('$'))}}
                        }}"
                    }}""".strip().replace("\t", "").replace("\n", "")
                },
                integration_responses=[
                    apigw.IntegrationResponse(
                        status_code="200",
                    )
                ],
            ),
        )

        child_resource = api.root.get_resource("suggestion2")
        if not child_resource:
            child_resource = api.root.add_resource("suggestion2")
        resource = child_resource

        img_suggest = resource.add_resource("{id}")

        img_suggest.add_method(
            "POST",
            integration=img_suggest_integration,
            authorizer=authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
            request_models={
                "application/json": img_suggest_request_model,
            },
            method_responses=[
                {
                    "statusCode": "200",
                }
            ],
            request_validator=validator,
        )

