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
    CfnOutput,
    aws_cognito as cognito,
    aws_iam as iam,
)
from constructs import Construct


class PACECognito(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        region: str,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.user_pool = cognito.UserPool(
            self,
            "UserPool",
            password_policy=cognito.PasswordPolicy(
              min_length=8,
              require_lowercase=True,
              require_uppercase=True,
              require_digits=True,
              require_symbols=True,
            ),
        )
        self.user_pool.node.default_child.user_pool_add_ons = cognito.CfnUserPool.UserPoolAddOnsProperty(
            advanced_security_mode="ENFORCED",
        )

        CfnOutput(
            self,
            "UserPoolId",
            value=self.user_pool.user_pool_id,
            export_name=f"{Stack.of(self).stack_name}{construct_id}UserPoolId",
        )

        self.user_pool_client = cognito.UserPoolClient(
            self,
            "UserPoolClient",
            user_pool=self.user_pool,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                admin_user_password=True,
                custom=True,
            ),
        )
        CfnOutput(
            self,
            "UserPoolClientId",
            value=self.user_pool_client.user_pool_client_id,
            export_name=f"{Stack.of(self).stack_name}{construct_id}UserPoolClientId",
        )

        self.identity_pool = cognito.CfnIdentityPool(
            self,
            "IdentityPool",
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                client_id=self.user_pool_client.user_pool_client_id,
                provider_name=self.user_pool.user_pool_provider_name
            )],
        )
        CfnOutput(
            self,
            "IdentityPoolId",
            value=self.identity_pool.ref,
            export_name=f"{Stack.of(self).stack_name}{construct_id}IdentityPoolId",
        )

        self.auth_user_role = iam.Role(
            self,
            "AuthenticatedUserRole",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                {
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": self.identity_pool.ref,
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated",
                    },
                },
                "sts:AssumeRoleWithWebIdentity",
            ),
        )
        
        self.unauth_user_role = iam.Role(
            self,
            "UnauthenticatedUserRole",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                {
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": self.identity_pool.ref,
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "unauthenticated",
                    },
                }
            )
        )

        self.identity_pool_role_attachment = cognito.CfnIdentityPoolRoleAttachment(
            self,
            "IdentityPoolRoleAttachment",
            identity_pool_id=self.identity_pool.ref,
            roles={
                "authenticated": self.auth_user_role.role_arn,
                "unauthenticated": self.unauth_user_role.role_arn,
            },
            role_mappings={
                "mapping": cognito.CfnIdentityPoolRoleAttachment.RoleMappingProperty(
                    type="Token",
                    ambiguous_role_resolution="AuthenticatedRole",
                    identity_provider="cognito-idp.{}.amazonaws.com/{}:{}".format(
                        region,
                        self.user_pool.user_pool_id,
                        self.user_pool_client.user_pool_client_id))
            }
        )
