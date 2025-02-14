from aws_cdk import (
    aws_iam as iam,
    Stack,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_connect as connect
)
from constructs import Construct

from lambdas import Lambdas
from topic import Topic
from databases import Tables

INSTANCE_ID             = "f5dbbb06-46e7-4435-beab-3b3303074765"


class ConnectCustomBotStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        stk = Stack.of(self)
        region = stk.region
        account_id = stk.account

        lambda_functions = Lambdas(self, "L")
        tables = Tables(self, "T")

        chat_streaming_topic = Topic(self, "CustomBotStreaming")

        lambda_functions.chat_bot.add_to_role_policy(iam.PolicyStatement(
            actions=["connect:StartChatContact", "connect:StopContactStreaming", "connect:CreateParticipant"],
            resources=[
                f"arn:aws:connect:*:{self.account}:instance/*",
                f"arn:aws:connect:*:{self.account}:instance/*/contact/*",
                f"arn:aws:connect:*:{self.account}:instance/*/contact-flow/*"
            ]))

        lambda_functions.chat_bot.add_environment("TABLE_NAME", tables.active_connections.table_name)
        lambda_functions.chat_bot.add_environment("INSTANCE_ID", INSTANCE_ID)
        lambda_functions.chat_bot.add_environment("TOPIC_ARN", chat_streaming_topic.topic.topic_arn)


        lambda_functions.start_bot.add_to_role_policy(iam.PolicyStatement(
            actions=["connect:StartChatContact", "connect:StartContactStreaming", "connect:CreateParticipant"],
            resources=[
                f"arn:aws:connect:*:{self.account}:instance/*",
                f"arn:aws:connect:*:{self.account}:instance/*/contact/*",
                f"arn:aws:connect:*:{self.account}:instance/*/contact-flow/*"
            ]))

        lambda_functions.start_bot.add_environment("TABLE_NAME", tables.active_connections.table_name)
        lambda_functions.start_bot.add_environment("INSTANCE_ID", INSTANCE_ID)
        lambda_functions.start_bot.add_environment("TOPIC_ARN", chat_streaming_topic.topic.topic_arn)

        tables.active_connections.grant_read_write_data(lambda_functions.start_bot)
        tables.active_connections.grant_read_write_data(lambda_functions.chat_bot)

        chat_streaming_topic.topic.add_subscription(
            subscriptions.LambdaSubscription(
                lambda_functions.chat_bot,
                filter_policy={
                    'ParticipantRole': sns.SubscriptionFilter.string_filter(
                        allowlist=['CUSTOMER']
                    ),
                    'Type': sns.SubscriptionFilter.string_filter(
                        allowlist=['MESSAGE']
                    )
                }
            )
        )

        chat_streaming_topic.allow_principal("connect.amazonaws.com")


        if INSTANCE_ID:
            instance_arn = f"arn:aws:connect:{region}:{account_id}:instance/{INSTANCE_ID}"

            connect.CfnIntegrationAssociation(
                self,
                "LStart_Bot",
                instance_id=instance_arn,
                integration_type="LAMBDA_FUNCTION",
                integration_arn=lambda_functions.start_bot.function_arn
            )

            connect.CfnIntegrationAssociation(
                self,
                "LChat_Bot",
                instance_id=instance_arn,
                integration_type="LAMBDA_FUNCTION",
                integration_arn=lambda_functions.chat_bot.function_arn
            )
