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

from aws_cdk import Stack
import aws_cdk as cdk
import aws_cdk.aws_iam as iam
from constructs import Construct

from cdk_nag import NagSuppressions

class CreateOpensearchRolesStack(Stack):
  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # Resources
    openSearchServerlessDataIndexingRole = iam.CfnRole(self, 'OpenSearchServerlessDataIndexingRole',
          description = 'Role used to index data into OpenSearch Serverless embeddings collection',
          assume_role_policy_document = {
            'Version': '2012-10-17',
            'Statement': [
              {
                'Effect': 'Allow',
                'Principal': {
                  'Service': [
                    'lambda.amazonaws.com',
                  ],
                },
                'Action': [
                  'sts:AssumeRole',
                ],
              },
            ],
          },
          policies = [
            {
              'policyName': 'OpenSearchAccess',
              'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [
                  {
                    'Sid': 'APIAccessAll',
                    'Effect': 'Allow',
                    'Action': [
                      'aoss:APIAccessAll',
                      'iam:ListUsers',
                    ],
                    'Resource': '*',
                  },
                ],
              },
            },
          ],
        )

    NagSuppressions.add_resource_suppressions(
      openSearchServerlessDataIndexingRole,
      [
        {
          "id": "AwsSolutions-IAM5",
          "reason": """Wildcard required for access to open search""",
        },
      ],
      True
    )

    openSearchServerlessDataQueryRole = iam.CfnRole(self, 'OpenSearchServerlessDataQueryRole',
          description = 'Role used to access OpenSearch Serverless embeddings collection',
          assume_role_policy_document = {
            'Version': '2012-10-17',
            'Statement': [
              {
                'Effect': 'Allow',
                'Principal': {
                  'Service': [
                    'lambda.amazonaws.com',
                  ],
                },
                'Action': [
                  'sts:AssumeRole',
                ],
              },
            ],
          },
        )

    # Outputs
    """
      OpenSearch serverless data indexing role ARN
    """
    self.data_indexing_role = openSearchServerlessDataIndexingRole.attr_arn
    cdk.CfnOutput(self, 'CfnOutputDataIndexingRole', 
      key = 'DataIndexingRole',
      description = 'OpenSearch serverless data indexing role ARN',
      value = str(self.data_indexing_role),
    )

    """
      OpenSearch serverless data querying role ARN
    """
    self.data_query_role = openSearchServerlessDataQueryRole.attr_arn
    cdk.CfnOutput(self, 'CfnOutputDataQueryRole', 
      key = 'DataQueryRole',
      description = 'OpenSearch serverless data querying role ARN',
      value = str(self.data_query_role),
    )



