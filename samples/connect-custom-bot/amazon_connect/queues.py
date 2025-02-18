from constructs import Construct
from aws_cdk import custom_resources as cr
from aws_cdk import aws_iam as iam


class ConnectQueues(Construct):
    def __init__(self, scope: Construct, id: str, instance_id: str) -> None:
        super().__init__(scope, id)

        # Create the custom resource that will list queues
        queue_list = cr.AwsCustomResource(
            self,
            "ListQueues",
            on_create=cr.AwsSdkCall(
                service="connect",
                action="listQueues",
                parameters={
                    "InstanceId": instance_id,
                    "MaxResults": 1  # Adjust as needed
                },
                physical_resource_id=cr.PhysicalResourceId.of("QueueList"),
                output_paths=["QueueSummaryList"]
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    actions=["connect:ListQueues"],
                    resources=[f"arn:aws:connect:*:*:instance/{instance_id}/*"]
                )
            ])
        )

        # Store the queue list as a property
        # self.queue_list = queue_list.get_response_field("QueueSummaryList")
        
        # Get the first queue from the list
        self.first_queue = queue_list.get_response_field("QueueSummaryList.0.Id")
        self.queues = queue_list.get_response_field("QueueSummaryList")
