from aws_cdk import (
    RemovalPolicy,
    aws_dynamodb as ddb
)
from constructs import Construct


REMOVAL_POLICY = RemovalPolicy.DESTROY

TABLE_CONFIG = dict (removal_policy=REMOVAL_POLICY, billing_mode= ddb.BillingMode.PAY_PER_REQUEST)

class Tables(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        self.active_connections = ddb.Table(
            self, "ChatbotContacts", 
            partition_key=ddb.Attribute(name="contactId", type=ddb.AttributeType.STRING),
            time_to_live_attribute='ttl',
            **TABLE_CONFIG)
