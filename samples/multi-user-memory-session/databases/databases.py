from aws_cdk import RemovalPolicy, custom_resources as cr, aws_dynamodb as ddb, CfnOutput
from constructs import Construct
import json




REMOVAL_POLICY = RemovalPolicy.DESTROY

TABLE_CONFIG = dict(
    removal_policy=REMOVAL_POLICY, billing_mode=ddb.BillingMode.PAY_PER_REQUEST
)


class Tables(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        self.orders = ddb.Table(
            self,
            "orders",
            partition_key=ddb.Attribute(
                name="order_number", type=ddb.AttributeType.STRING
            ),
            **TABLE_CONFIG,
        )


        with open("databases/orders.json") as f:
            sample_data = json.load(f)

        parameters = {
            "RequestItems": {
                self.orders.table_name: [
                    {"PutRequest": {"Item": item}}
                    for item in sample_data.get("Items")
                ]
            }
        }

        cr.AwsCustomResource(
            self,
            "BatchWriteItem",
            on_update=cr.AwsSdkCall( 
                service="dynamodb",
                action="BatchWriteItem",
                parameters=parameters,
                physical_resource_id=cr.PhysicalResourceId.of(f"BatchWriteItem-{self.orders.table_name}"),
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
        )


        CfnOutput(self, "SampleData", value=json.dumps(sample_data))