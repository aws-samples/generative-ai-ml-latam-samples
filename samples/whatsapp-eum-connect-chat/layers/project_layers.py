import json
from constructs import Construct

from aws_cdk import (
    aws_lambda as _lambda

)
# Boto 3 1.35.69 has End User Social Messagin support!
# This layer provides boto3 version to lambda environment
class Boto3_1_35_69(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.layer = _lambda.LayerVersion(
            self, "Boto3.1.35.69", code=_lambda.Code.from_asset("./layers/boto3.1.35.69.zip"),
            compatible_runtimes = [_lambda.Runtime.PYTHON_3_10, _lambda.Runtime.PYTHON_3_11, _lambda.Runtime.PYTHON_3_13, _lambda.Runtime.PYTHON_3_12 ], 
            description = 'Boto3 con Social Messaging')

    

    



class TranscribeClient(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.layer = _lambda.LayerVersion(
            self, "Transcribe Streaming", code=_lambda.Code.from_asset("./layers/transcribe-client.zip"),
            compatible_runtimes = [_lambda.Runtime.PYTHON_3_10, _lambda.Runtime.PYTHON_3_11, _lambda.Runtime.PYTHON_3_13, _lambda.Runtime.PYTHON_3_12 ], 
            description = 'Transcribe Streaming')

    