from aws_cdk import aws_connect as connect
from constructs import Construct


class ContactFlow(Construct):

    def __init__(self, scope: Construct, construct_id: str,instance_arn, cf_name, cf_type, cf_content,cf_description,  **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_connect/CfnContactFlow.html
        self.resource = connect.CfnContactFlow(self, "CF",
            content=cf_content,
            instance_arn=instance_arn,
            name=cf_name,
            type=cf_type,
            # the properties below are optional
            description= cf_description,
            state="ACTIVE",
        )