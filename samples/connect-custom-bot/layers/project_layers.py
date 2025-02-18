import json
from constructs import Construct

from aws_cdk import (
    aws_lambda as _lambda

)

class Boto3_1_36_21(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.layer = _lambda.LayerVersion(
            self, "Boto3.1.36.21", code=_lambda.Code.from_asset("./layers/boto3.1.36.21.zip"),
            compatible_runtimes = [_lambda.Runtime.PYTHON_3_10, _lambda.Runtime.PYTHON_3_11, _lambda.Runtime.PYTHON_3_13, _lambda.Runtime.PYTHON_3_12 ], 
            description = 'Boto3 con Bedrock Multi Agent')

    

