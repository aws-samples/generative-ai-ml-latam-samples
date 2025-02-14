import aws_cdk as core
import aws_cdk.assertions as assertions

from connect_custom_bot.connect_custom_bot_stack import ConnectCustomBotStack

# example tests. To run these tests, uncomment this file along with the example
# resource in connect_custom_bot/connect_custom_bot_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ConnectCustomBotStack(app, "connect-custom-bot")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
