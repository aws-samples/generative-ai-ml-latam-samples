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
    aws_apigateway as apigateway,
    aws_cognito as cognito,
    aws_logs as logs,
    aws_lambda,
    aws_wafv2 as waf,
)
from constructs import Construct

from cdk_nag import NagSuppressions, NagPackSuppression


class PACEApiGateway(Construct):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            region: str,
            user_pool: cognito.UserPool,
            **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.cognito_authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self,
            "CognitoUserPoolAuthorizer",
            cognito_user_pools=[user_pool],
        )

        self.log_group = logs.LogGroup(self, "LogGroup")

        self.rest_api = apigateway.RestApi(
            self,
            "RestApi",
            cloud_watch_role=True,
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=[* apigateway.Cors.DEFAULT_HEADERS, "Access-Control-Allow-Origin"],
            ),
            deploy_options=apigateway.StageOptions(
                logging_level=apigateway.MethodLoggingLevel.INFO,
                access_log_destination=apigateway.LogGroupLogDestination(self.log_group),
                access_log_format=apigateway.AccessLogFormat.clf(),
                tracing_enabled=True,
                data_trace_enabled=False,
                stage_name="api",
            ),
            endpoint_export_name=f"{Stack.of(self).stack_name}{construct_id}RestApiEndpoint",
        )

        self.request_body_validator = apigateway.RequestValidator(
            self,
            "RequestBodyValidator",
            rest_api=self.rest_api,
            request_validator_name="Validate body",
            validate_request_body=True,
            validate_request_parameters=False,
        )

        # Choose a validator based on your needs

        self.request_params_validator = apigateway.RequestValidator(
            self,
            "RequestParametersValidator",
            rest_api=self.rest_api,
            request_validator_name="Validate query string parameters",
            validate_request_body=False,
            validate_request_parameters=True,
        )

        self.request_body_params_validator = apigateway.RequestValidator(
            self,
            "RequestBodyParametersValidator",
            rest_api=self.rest_api,
            request_validator_name="Validate body and query string parameters",
            validate_request_body=True,
            validate_request_parameters=True,
        )

        self.web_acl = waf.CfnWebACL(
            self,
            "WebACL",
            scope="REGIONAL",
            default_action=waf.CfnWebACL.DefaultActionProperty(
                allow=waf.CfnWebACL.AllowActionProperty(),
            ),
            visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                sampled_requests_enabled=True,
                metric_name=construct_id + "-PACEWebACL",
            ),
            rules=[
                waf.CfnWebACL.RuleProperty(
                    name="AWSManagedRules",
                    priority=0,
                    statement=waf.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=waf.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesCommonRuleSet",
                            excluded_rules=[],
                        )
                    ),
                    override_action=waf.CfnWebACL.OverrideActionProperty(
                        count={},
                    ),
                    visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        sampled_requests_enabled=True,
                        metric_name=construct_id + "-PACEWebACL-AWSManagedRules",
                    ),
                )
            ],
        )

        self.web_acl_assoc = waf.CfnWebACLAssociation(
            self,
            "WebACLAssociation",
            web_acl_arn=self.web_acl.attr_arn,
            resource_arn="arn:aws:apigateway:{}::/restapis/{}/stages/{}".format(
                region,
                self.rest_api.rest_api_id,
                self.rest_api.deployment_stage.stage_name,
            ),
        )

        NagSuppressions.add_resource_suppressions(
            construct=self.rest_api,
            suppressions=[
                NagPackSuppression(
                    id="AwsSolutions-IAM4",
                    reason="AmazonAPIGatewayPushToCloudWatchLogs",
                    applies_to=[
                        "Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
                    ],
                ),
            ],
            apply_to_children=True,
        )

    def add_method(
            self,
            resource_path: str,
            http_method: str,
            lambda_function: aws_lambda.Function,
            request_validator: apigateway.RequestValidator,
            request_parameters: typing.Optional[typing.Mapping[str, bool]] = None,
            **kwargs
    ):
        path_parts = list(filter(bool, resource_path.split("/")))
        resource = self.rest_api.root
        for path_part in path_parts:
            child_resource = resource.get_resource(path_part)
            if not child_resource:
                child_resource = resource.add_resource(path_part)
            resource = child_resource

        resource.add_method(
            http_method=http_method,
            integration=apigateway.LambdaIntegration(lambda_function),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
            request_parameters=request_parameters,
            request_validator=request_validator,
            **kwargs
        )

        # Add Cognito auth to all methods except OPTIONS to allow for CORS header lookups
        for method in self.rest_api.methods:
            resource = method.node.find_child("Resource")
            if method.http_method == "OPTIONS":
                resource.add_property_override("AuthorizationType", apigateway.AuthorizationType.NONE)
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
                resource.add_property_override("AuthorizationType", apigateway.AuthorizationType.COGNITO)
                resource.add_property_override("AuthorizerId", self.cognito_authorizer.authorizer_id)

    def add_method_async(
            self,
            resource_path: str,
            http_method: str,
            lambda_function: aws_lambda.Function,
            request_validator: apigateway.RequestValidator,
            request_parameters: typing.Optional[typing.Mapping[str, bool]] = None,
            **kwargs
    ):
        request_template = """##  See https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-mapping-template-reference.html
            ##  This template will pass through all parameters including path, querystring, header, stage variables, and context through to the integration endpoint via the body/payload
            #set($allParams = $input.params())
            #set($pathParams = $allParams.path)
            {
            "httpMethod": "$context.httpMethod",
            "uid": "$pathParams.id"
            }""".replace(' ', '').strip()

        path_parts = list(filter(bool, resource_path.split("/")))
        resource = self.rest_api.root
        for path_part in path_parts:
            child_resource = resource.get_resource(path_part)
            if not child_resource:
                child_resource = resource.add_resource(path_part)
            resource = child_resource

        resource.add_method(
            http_method=http_method,
            integration=apigateway.LambdaIntegration(
                lambda_function,
                request_parameters={"integration.request.header.X-Amz-Invocation-Type" : "'Event'"},
                proxy=False,
                passthrough_behavior=apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES,
                request_templates={"application/json": request_template},
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent,Access-Control-Allow-Origin'",
                            "method.response.header.Access-Control-Allow-Methods": "'OPTIONS,GET,PUT,POST,DELETE,PATCH,HEAD'",
                            "method.response.header.Access-Control-Allow-Origin": "'*'"
                        }
                    ),
                    apigateway.IntegrationResponse(
                        status_code="202",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent,Access-Control-Allow-Origin'",
                            "method.response.header.Access-Control-Allow-Methods": "'OPTIONS,GET,PUT,POST,DELETE,PATCH,HEAD'",
                            "method.response.header.Access-Control-Allow-Origin": "'*'"
                        }
                    ),
                ]
            ),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
            request_parameters=request_parameters,
            request_validator=request_validator,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="202",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ],
            **kwargs
        )

        # Add Cognito auth to all methods except OPTIONS to allow for CORS header lookups
        for method in self.rest_api.methods:
            resource = method.node.find_child("Resource")
            if method.http_method == "OPTIONS":
                resource.add_property_override("AuthorizationType", apigateway.AuthorizationType.NONE)
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
                resource.add_property_override("AuthorizationType", apigateway.AuthorizationType.COGNITO)
                resource.add_property_override("AuthorizerId", self.cognito_authorizer.authorizer_id)


    def add_method_async2(
            self,
            resource_path: str,
            http_method: str,
            lambda_function: aws_lambda.Function,
            request_validator: apigateway.RequestValidator,
            request_parameters: typing.Optional[typing.Mapping[str, bool]] = None,
            **kwargs
    ):
        request_template = """##  See https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-mapping-template-reference.html
            ##  This template will pass through all parameters including path, querystring, header, stage variables, and context through to the integration endpoint via the body/payload
            #set($allParams = $input.params())
            #set($pathParams = $allParams.path)
            {
            "httpMethod": "$context.httpMethod",
            "uid": "$pathParams.id",
            "body": $input.body
            }""".replace(' ', '').strip()

        path_parts = list(filter(bool, resource_path.split("/")))
        resource = self.rest_api.root
        for path_part in path_parts:
            child_resource = resource.get_resource(path_part)
            if not child_resource:
                child_resource = resource.add_resource(path_part)
            resource = child_resource

        resource.add_method(
            http_method=http_method,
            integration=apigateway.LambdaIntegration(
                lambda_function,
                request_parameters={"integration.request.header.X-Amz-Invocation-Type" : "'Event'"},
                proxy=False,
                passthrough_behavior=apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES,
                request_templates={"application/json": request_template},
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Headers":"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent,Access-Control-Allow-Origin'",
                            "method.response.header.Access-Control-Allow-Methods":"'OPTIONS,GET,PUT,POST,DELETE,PATCH,HEAD'",
                            "method.response.header.Access-Control-Allow-Origin":"'*'"
                        }
                    ),
                    apigateway.IntegrationResponse(
                        status_code="202",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent,Access-Control-Allow-Origin'",
                            "method.response.header.Access-Control-Allow-Methods": "'OPTIONS,GET,PUT,POST,DELETE,PATCH,HEAD'",
                            "method.response.header.Access-Control-Allow-Origin": "'*'"
                        }
                    ),
                ]
            ),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
            request_parameters=request_parameters,
            request_validator=request_validator,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="202",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ],
            **kwargs
        )

        # Add Cognito auth to all methods except OPTIONS to allow for CORS header lookups
        for method in self.rest_api.methods:
            resource = method.node.find_child("Resource")
            if method.http_method == "OPTIONS":
                resource.add_property_override("AuthorizationType", apigateway.AuthorizationType.NONE)
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
                resource.add_property_override("AuthorizationType", apigateway.AuthorizationType.COGNITO)
                resource.add_property_override("AuthorizerId", self.cognito_authorizer.authorizer_id)
