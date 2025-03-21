from aws_cdk import RemovalPolicy, custom_resources as cr, aws_dynamodb as ddb, CfnOutput
from constructs import Construct
import json




REMOVAL_POLICY = RemovalPolicy.DESTROY

TABLE_CONFIG = dict(
    removal_policy=REMOVAL_POLICY, billing_mode=ddb.BillingMode.PAY_PER_REQUEST
)

"""
Class for creating and managing DynamoDB tables used in the application.
"""
class Tables(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """
        Initialize the database tables construct.
        
        Args:
            scope: The scope in which to create the tables
            construct_id: The ID of this construct
            kwargs: Additional keyword arguments
        """
        super().__init__(scope, construct_id, **kwargs)

        self.tickets = ddb.Table(
            self,
            "tickets",
            partition_key=ddb.Attribute(
                name="issue_number", type=ddb.AttributeType.STRING
            ),
            **TABLE_CONFIG,
        )


        self.orders = ddb.Table(
            self,
            "orders",
            partition_key=ddb.Attribute(
                name="order_number", type=ddb.AttributeType.STRING
            ),
            **TABLE_CONFIG,
        )

        self.orders.add_global_secondary_index(
            index_name="phone_number",
            partition_key=ddb.Attribute(
                name="phone_number", type=ddb.AttributeType.STRING
            ),
        )

        #Load table with sample data

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

        # Create  table from sample data
        markdown_table = "\n\t Order Number  \t ID Number \t Status \t Delivery Date \t\n"        
        for item in sample_data["Items"]:
            markdown_table += f"\t {item['order_number']['S']} \t {item['identity_document_number']['S']} \t "
            markdown_table += f"{item['status']['S']} \t {item['delivery_date']['S']} \t\n"
        
        # Output the table
        CfnOutput(self, "SampleOrdersTable",
            value=markdown_table,
            description="Sample orders data in markdown table format"
        )
