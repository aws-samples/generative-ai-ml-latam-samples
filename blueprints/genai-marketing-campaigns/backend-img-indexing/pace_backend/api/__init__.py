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
    Stack,
    aws_iam as iam,
    aws_s3 as s3,
    aws_stepfunctions as sfn
)

from constructs import Construct

from cdk_nag import NagSuppressions

import pace_constructs as pace

from pace_backend.api.IndexImg import IndexImg
from pace_backend.api.DownloadImg import DownloadImg

class IndexImgAPI(Construct):
    """A Construct to create an API to index images"""

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            imgs_bucket: s3.IBucket,
            workflow_machine: sfn.IStateMachine
    ) -> None:
        super().__init__(scope, construct_id)

        # Create cognito user pool to authenticate APIs
        self.cognito = pace.PACECognito(
            self,
            "IndexImgCognito",
            region=Stack.of(self).region,
        )

        # Create API GW to manage indexing API
        self.apigw = pace.PACEApiGateway(
            self,
            "ApiGateway",
            region=Stack.of(self).region,
            user_pool=self.cognito.user_pool,
        )

        # Define API methods

        # Create method for uploading image
        self.api_role = iam.Role(
            self, "ApiRole", assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com")
        )

        imgs_bucket.grant_write(self.api_role)
        self.apigw.add_s3_method(
            resource_path="/imgMetaIndex/upload/{folder}/{key}",
            http_method="PUT",
            request_validator=self.apigw.request_body_params_validator,
            bucket_name=imgs_bucket.bucket_name,
            execution_role=self.api_role,
            request_parameters={
                "method.request.path.folder": True,
                "method.request.path.key": True,
                "method.request.header.Content-Type": True,
                "method.request.header.Accept": True,
            }
        )
        NagSuppressions.add_resource_suppressions(
            self.api_role,
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": """Policy implemented by CDK""",
                },
            ],
            True,
        )

        #Add integration with workflow state machine to index data
        IndexImg(
            self,
            "IndexImgMethod",
            api=self.apigw.rest_api,
            validator=self.apigw.request_body_params_validator,
            api_role=self.api_role,
            authorizer=self.apigw.cognito_authorizer,
            workflow_machine=workflow_machine,
        )

        #S3 proxy integration to download files
        DownloadImg(
            self,
            "DownloadImgMethod",
            api_gw=self.apigw,
            api_role=self.api_role,
            imgs_bucket=imgs_bucket
        )