import json
from aws_cdk import (
    Duration,
    aws_iam as iam,
    aws_lambda,
    aws_ssm as ssm
)


from constructs import Construct


LAMBDA_TIMEOUT = 900

BASE_LAMBDA_CONFIG = dict(
    timeout=Duration.seconds(LAMBDA_TIMEOUT),
    memory_size=512,
    
    runtime=aws_lambda.Runtime.PYTHON_3_13,
    architecture=aws_lambda.Architecture.ARM_64,
    tracing=aws_lambda.Tracing.ACTIVE,
)


from layers import Boto3_1_35_69, TranscribeClient

class Lambdas(Construct):
    def __init__(
        self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        BotoLayer = Boto3_1_35_69(self, "Boto3_1_35_69")
        TranscribeLayer = TranscribeClient(self, "TranscribeLayer")

        # ======================================================================
        # Lambda Envia la notificación al topoc
        # ======================================================================
        self.whatsapp_event_handler = aws_lambda.Function(
            self,
            "WABAEventHandler",
            code=aws_lambda.Code.from_asset("./lambdas/code/whatsapp_event_handler/"),
            handler="lambda_function.lambda_handler",
            layers=[BotoLayer.layer, TranscribeLayer.layer],
            **BASE_LAMBDA_CONFIG,
        )

