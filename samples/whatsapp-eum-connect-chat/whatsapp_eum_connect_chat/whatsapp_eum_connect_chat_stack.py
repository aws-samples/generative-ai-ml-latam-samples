from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    CfnOutput,
    aws_sns as sns,
)
from constructs import Construct

from lambdas import Lambdas
from topic import Topic
from databases import Tables


INSTANCE_ID = "INSTANCE_ID"
CONTACT_FLOW_ID = "CONTACT_FLOW_ID"
CHAT_DURATION_MINUTES = 60


class WhatsappEumConnectChatStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        stk = Stack.of(self)
        region = stk.region
        account_id = stk.account

        lambda_functions = Lambdas(self, "L")
        sns_topic_in = Topic(self,"IN",lambda_function=lambda_functions.whatsapp_event_handler)
        sns_topic_out = Topic(self, "OUT", lambda_function=lambda_functions.connect_event_handler)

        tables = Tables(self, "T")
        # amazonq-ignore-next-line
        s3_bucket = s3.Bucket(self, "S3", removal_policy=RemovalPolicy.DESTROY)

        # Lambda 1 Permissions and Env
        lambda_functions.whatsapp_event_handler.add_environment(
            "TABLE_NAME", tables.active_connections.table_name
        )
        lambda_functions.whatsapp_event_handler.add_environment(
            "BUCKET_NAME", s3_bucket.bucket_name
        )
        lambda_functions.whatsapp_event_handler.add_environment(
            "VOICE_PREFIX", "voice_"
        )
        lambda_functions.whatsapp_event_handler.add_environment(
            "INSTANCE_ID", INSTANCE_ID
        )
        lambda_functions.whatsapp_event_handler.add_environment(
            "CONTACT_FLOW_ID", CONTACT_FLOW_ID
        )
        lambda_functions.whatsapp_event_handler.add_environment(
            "CHAT_DURATION_MINUTES", str(CHAT_DURATION_MINUTES)
        )
        lambda_functions.whatsapp_event_handler.add_environment(
            "TOPIC_ARN", sns_topic_out.topic.topic_arn
        )

        lambda_functions.whatsapp_event_handler.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "social-messaging:SendWhatsAppMessage",
                    "social-messaging:GetWhatsAppMessageMedia",
                ],
                resources=[
                    f"arn:aws:social-messaging:{region}:{account_id}:phone-number-id/*"
                ],
            )
        )
        lambda_functions.whatsapp_event_handler.add_to_role_policy(
            iam.PolicyStatement(actions=["transcribe:*"], resources=["*"])
        )

        s3_bucket.grant_read_write(lambda_functions.whatsapp_event_handler)

        # Lambda 2 Permissions and Env

        lambda_functions.connect_event_handler.add_environment(
            "TABLE_NAME", tables.active_connections.table_name
        )

        lambda_functions.connect_event_handler.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "social-messaging:SendWhatsAppMessage",
                    "social-messaging:GetWhatsAppMessageMedia",
                ],
                resources=[
                    f"arn:aws:social-messaging:{region}:{account_id}:phone-number-id/*"
                ],
            )
        )
        lambda_functions.whatsapp_event_handler.add_to_role_policy(
            iam.PolicyStatement(
                actions=["connect:StartChatContact", "connect:StartContactStreaming"],
                resources=[
                    f"arn:aws:connect:*:{self.account}:instance/*",
                    f"arn:aws:connect:*:{self.account}:instance/*/contact/*",
                    f"arn:aws:connect:*:{self.account}:instance/*/contact-flow/*",
                ],
            )
        )

        # Tables permissions
        tables.active_connections.grant_full_access(
            lambda_functions.whatsapp_event_handler
        )
        tables.active_connections.grant_full_access(
            lambda_functions.connect_event_handler
        )

        # Principal permissions
        sns_topic_in.allow_principal("social-messaging.amazonaws.com")
        sns_topic_out.allow_principal("connect.amazonaws.com")

        CfnOutput(self, "TopicArn", value=sns_topic_in.topic.topic_arn)
