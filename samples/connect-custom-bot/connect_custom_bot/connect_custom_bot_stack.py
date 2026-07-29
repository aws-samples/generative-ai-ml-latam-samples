from aws_cdk import (
    aws_iam as iam,
    Fn,
    Stack,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_connect as connect,
    CfnParameter
)
from constructs import Construct

from lambdas import Lambdas
from topic import Topic
from databases import Tables
from amazon_connect import  ConnectQueues, ConnectInstance

INSTANCE_ID = "INSTANCE_ID"
AGENT_ID = "AGENT_ID"
AGENT_ALIAS_ID = "TSTALIASID"


class ConnectCustomBotStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        stk = Stack.of(self)
        region = stk.region
        account_id = stk.account

        INSTANCE_ID = CfnParameter(self, "instanceId",  type="String",
        description="The Amazon Connect instance Id to associate the stack with.").value_as_string        

        lambda_functions = Lambdas(self, "L")
        tables = Tables(self, "T")

        chat_streaming_topic = Topic(self, "CustomBotStreaming")

        lambda_functions.chat_bot.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "connect:StartChatContact",
                    "connect:StopContactStreaming",
                    "connect:CreateParticipant",
                    "connect:UpdateContactAttributes",
                ],
                resources=[
                    f"arn:aws:connect:*:{self.account}:instance/*",
                    f"arn:aws:connect:*:{self.account}:instance/*/contact/*",
                    f"arn:aws:connect:*:{self.account}:instance/*/contact-flow/*",
                ],
            )
        )

        lambda_functions.chat_bot.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:Invoke*"],
                resources=[
                    f"arn:aws:bedrock:{region}:{account_id}:agent*",
                    "arn:aws:bedrock:us-east-1::foundation-model/*",
                    "arn:aws:bedrock:us-east-2::foundation-model/*",
                    "arn:aws:bedrock:us-west-2::foundation-model/*",
                    f"arn:aws:bedrock:{region}:{account_id}:inference-profile/*",
                ],
            )
        )

        lambda_functions.chat_bot.add_environment(
            "TABLE_NAME", tables.active_connections.table_name
        )
        lambda_functions.chat_bot.add_environment("INSTANCE_ID", INSTANCE_ID)
        lambda_functions.chat_bot.add_environment(
            "TOPIC_ARN", chat_streaming_topic.topic.topic_arn
        )
        lambda_functions.chat_bot.add_environment("AGENT_ID", AGENT_ID)
        lambda_functions.chat_bot.add_environment("AGENT_ALIAS_ID", AGENT_ALIAS_ID)

        lambda_functions.start_bot.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "connect:StartChatContact",
                    "connect:StartContactStreaming",
                    "connect:CreateParticipant",
                ],
                resources=[
                    f"arn:aws:connect:*:{self.account}:instance/*",
                    f"arn:aws:connect:*:{self.account}:instance/*/contact/*",
                    f"arn:aws:connect:*:{self.account}:instance/*/contact-flow/*",
                ],
            )
        )

        lambda_functions.start_bot.add_environment(
            "TABLE_NAME", tables.active_connections.table_name
        )
        lambda_functions.start_bot.add_environment("INSTANCE_ID", INSTANCE_ID)
        lambda_functions.start_bot.add_environment(
            "TOPIC_ARN", chat_streaming_topic.topic.topic_arn
        )

        tables.active_connections.grant_read_write_data(lambda_functions.start_bot)
        tables.active_connections.grant_read_write_data(lambda_functions.chat_bot)

        chat_streaming_topic.topic.add_subscription(
            subscriptions.LambdaSubscription(
                lambda_functions.chat_bot,
                filter_policy={
                    "ParticipantRole": sns.SubscriptionFilter.string_filter(
                        allowlist=["CUSTOMER"]
                    ),
                    "Type": sns.SubscriptionFilter.string_filter(allowlist=["MESSAGE"]),
                },
            )
        )

        chat_streaming_topic.allow_principal("connect.amazonaws.com")

        if INSTANCE_ID:
            ac_instance = ConnectInstance(self, "AC", instance_id=INSTANCE_ID)
            ac_instance.lambda_association("start_bot", lambda_functions.start_bot)

            with open("amazon_connect/flow_definition.json", "r") as f:
                flow_definition = f.read()

            connect_queues = ConnectQueues(self, "Q", instance_id=INSTANCE_ID)

            flow_definition = Fn.sub(
                body=flow_definition,
                variables={
                    "QUEUE_ID": str(connect_queues.first_queue),
                    "INSTANCE_ID": INSTANCE_ID,
                    "REPLACE_LAMBDA_FUNCTION": lambda_functions.start_bot.function_arn,
                },
            )

            ac_instance.create_contact_flow(
                cf_name="Custom Bot Flow via CDK",
                cf_type="CONTACT_FLOW",
                cf_content=flow_definition,
                cf_description="Custom Bot that invokes high latency Agents with escalation",
            )

