import aws_cdk as core
import aws_cdk.assertions as assertions

from whatsapp_eum_connect_chat.whatsapp_eum_connect_chat_stack import WhatsappEumConnectChatStack

# example tests. To run these tests, uncomment this file along with the example
# resource in whatsapp_connect_custom_bot/whatsapp_connect_custom_bot_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = WhatsappEumConnectChatStack(app, "whatsapp-connect-custom-bot")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
