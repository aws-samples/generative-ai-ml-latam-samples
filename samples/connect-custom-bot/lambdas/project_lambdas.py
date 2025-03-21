import json
from aws_cdk import (
    Duration,
    aws_iam as iam,
    aws_lambda,
    aws_ssm as ssm
)


from constructs import Construct
from layers import Boto3_1_36_21


LAMBDA_TIMEOUT = 900

BASE_LAMBDA_CONFIG = dict(
    timeout=Duration.seconds(LAMBDA_TIMEOUT),
    memory_size=512,
    runtime=aws_lambda.Runtime.PYTHON_3_12,
    architecture=aws_lambda.Architecture.ARM_64,
    tracing=aws_lambda.Tracing.ACTIVE,
)


class Lambdas(Construct):
    def __init__(
        self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        BotoLayer = Boto3_1_36_21(self, "Boto3_1_36_21")

        # ======================================================================
        # Comienza el custom bot
        # ======================================================================
        self.start_bot = aws_lambda.Function(
            self,
            "StartBot",
            code=aws_lambda.Code.from_asset("./lambdas/code/start_bot/"),
            handler="lambda_function.lambda_handler",
            **BASE_LAMBDA_CONFIG,
        )

        # ======================================================================
        # Chat Bot responses
        # ======================================================================
        self.chat_bot = aws_lambda.Function(
            self,
            "Chatbot",
            code=aws_lambda.Code.from_asset("./lambdas/code/chat_bot/"),
            handler="lambda_function.lambda_handler",
            layers=[BotoLayer.layer], # This is for multi agent support 
            **BASE_LAMBDA_CONFIG,
        )


