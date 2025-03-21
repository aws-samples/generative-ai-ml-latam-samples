from aws_cdk import aws_connect as connect, Stack, aws_lambda
from constructs import Construct

class ConnectInstance(Construct):

    def __init__(
        self, scope: Construct, construct_id: str, instance_id, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        stk = Stack.of(self)
        region = stk.region
        account_id = stk.account

        self.instance_arn = (
            f"arn:aws:connect:{region}:{account_id}:instance/{instance_id}"
        )

    def lambda_association(self, id, lambda_function: aws_lambda.Function):
        return connect.CfnIntegrationAssociation(
            self,
            id,
            instance_id=self.instance_arn,
            integration_type="LAMBDA_FUNCTION",
            integration_arn=lambda_function.function_arn,
        )
    
    def create_contact_flow(self, cf_name, cf_type, cf_content, cf_description):
        return connect.CfnContactFlow(
            self,
            cf_name,
            content=cf_content,
            instance_arn=self.instance_arn,
            name=cf_name,
            type=cf_type,
            description=cf_description or "",
            state="ACTIVE",
        )
