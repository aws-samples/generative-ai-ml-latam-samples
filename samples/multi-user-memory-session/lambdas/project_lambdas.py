from aws_cdk import Duration, aws_lambda
from constructs import Construct

LAMBDA_TIMEOUT = 900

BASE_LAMBDA_CONFIG = dict(
    timeout=Duration.seconds(LAMBDA_TIMEOUT),
    runtime=aws_lambda.Runtime.PYTHON_3_12,
    architecture=aws_lambda.Architecture.ARM_64,
    tracing=aws_lambda.Tracing.ACTIVE,
    memory_size=512,
)


class Lambdas(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ======================================================================
        # Orders interaction ( get order)
        # ======================================================================

        self.orders = aws_lambda.Function(
            self,
            "Orders",
            handler="lambda_function.lambda_handler", 
            code=aws_lambda.Code.from_asset("./lambdas/code/orders/"),
            **BASE_LAMBDA_CONFIG,
        )