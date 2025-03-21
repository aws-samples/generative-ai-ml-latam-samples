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


"""
Class for managing all Lambda functions used in the project.
"""
class Lambdas(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """
        Initialize the Lambda functions construct.
        
        Args:
            scope: The scope in which to create the Lambda functions
            construct_id: The ID of this construct
            kwargs: Additional keyword arguments
        """
        super().__init__(scope, construct_id, **kwargs)

        # ======================================================================
        # Tickets interaction (cut ticket, get ticket)
        # ======================================================================
        
        self.tickets = aws_lambda.Function(
            self,
            "Tickets",
            handler="lambda_function.lambda_handler", 
            code=aws_lambda.Code.from_asset("./lambdas/code/tickets/"),
            **BASE_LAMBDA_CONFIG,
        )
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