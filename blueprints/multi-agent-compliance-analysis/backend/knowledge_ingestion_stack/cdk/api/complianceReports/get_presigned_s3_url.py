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
    aws_lambda,
    aws_apigateway as apigateway,
)
from constructs import Construct
from cdk_nag import NagSuppressions, NagPackSuppression


class GetPresignedS3URL(Construct):
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
    ) -> None:
        super().__init__(scope, id)

        resource = api.root

        path_parts = list(filter(bool, resource_path.split("/")))
        for path_part in path_parts:
            child_resource = resource.get_resource(path_part)
            if not child_resource:
                child_resource = resource.add_resource(path_part)
            resource = child_resource

        integrator = apigateway.LambdaIntegration(lambda_function)

        resource.add_method(
            http_method=http_method,
            integration=integrator,
            authorizer=cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
            request_validator=request_validator,
        )