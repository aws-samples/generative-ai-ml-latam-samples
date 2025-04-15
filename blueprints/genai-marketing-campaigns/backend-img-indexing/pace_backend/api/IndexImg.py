# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0


from aws_cdk import (
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_stepfunctions as sfn,
    Stack,
)
from constructs import Construct

from cdk_nag import NagSuppressions, NagPackSuppression

index_img_request_template = """{\\"img_key\\": \\"$inputRoot.key\\",
                        \\"metadata\\": 
                        {
                        \\"node\\": \\"$inputMetadata.node\\", 
                        \\"results\\": $inputMetadata.results,
                        \\"objective\\": \\"$inputMetadata.objective\\"
                        } 
                    }""".replace('\n', '').replace(" ", "").strip()


class IndexImg(Construct):
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

        index_img_request_model = api.add_model(
            "IndexImageRequest",
            schema=apigw.JsonSchema(
                schema=apigw.JsonSchemaVersion.DRAFT4,
                title="IndexImageRequest",
                type=apigw.JsonSchemaType.OBJECT,
                properties={
                    "key": apigw.JsonSchema(type=apigw.JsonSchemaType.STRING),
                    "metadata": apigw.JsonSchema(
                        type=apigw.JsonSchemaType.OBJECT,
                        properties={
                            "results": apigw.JsonSchema(type=apigw.JsonSchemaType.NUMBER),
                            "node": apigw.JsonSchema(type=apigw.JsonSchemaType.STRING),
                            "objective": apigw.JsonSchema(type=apigw.JsonSchemaType.STRING)
                        },
                        required=["results", "node", "objective"],
                    ),
                },
                required=["key", "metadata"],
            ),
            content_type="application/json",
        )

        img_index_integration = apigw.AwsIntegration(
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
                    #set($inputMetadata = $input.path('$.metadata'))
                    {{
                        "stateMachineArn": "{workflow_machine.state_machine_arn}",
                        "input": "{index_img_request_template}"
                    }}"""
                },
                integration_responses=[
                    apigw.IntegrationResponse(
                        status_code="200",
                    )
                ],
            ),
        )

        child_resource = api.root.get_resource("imgMetaIndex")
        if not child_resource:
            child_resource = api.root.add_resource("imgMetaIndex")
        resource = child_resource

        img_index = resource.add_resource("indexImage")

        img_index.add_method(
            "POST",
            integration=img_index_integration,
            authorizer=authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
            method_responses=[
                {
                    "statusCode": "200",
                }
            ],
            request_models={
                "application/json": index_img_request_model,
            },
            request_validator=validator,
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

