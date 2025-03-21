import aws_cdk as core
import aws_cdk.assertions as assertions

from multi_agent_collaboration.multi_agent_collaboration_stack import MultiAgentCollaborationStack

# example tests. To run these tests, uncomment this file along with the example
# resource in multi_agent_collaboration/multi_agent_collaboration_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = MultiAgentCollaborationStack(app, "multi-agent-collaboration")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
