from aws_cdk import custom_resources as cr, aws_iam as iam, CfnOutput
from aws_cdk.aws_bedrock import CfnAgent, CfnAgentAlias
from aws_cdk import aws_ssm as ssm
from datetime import datetime
from constructs import Construct


class MultiAgentCollaboration(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        agent_supervisor: CfnAgent,
        agent_collaborator_alias: CfnAgentAlias,
        agent_supervisor_version="DRAFT",
        collaboration_instruction="You are a helpful collaborator",
        collaborator_name="simple-collaborator",
        relay_conversation_history="TO_COLLABORATOR",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.alias_arn = agent_collaborator_alias.attr_agent_alias_arn
        self.agent_id = agent_supervisor.attr_agent_id
        self.agent_version = agent_supervisor_version
        self.collaboration_instruction = collaboration_instruction
        self.collaborator_name = collaborator_name
        self.relay_conversation_history = relay_conversation_history
        self.collaborator_id = None
        self.physical_resource_id = cr.PhysicalResourceId.of(f"{self.agent_id}::MULTI::{self.collaborator_name}")


        self.collaboration_cr = cr.AwsCustomResource(
            self,
            "AssocAgent",
            on_create=cr.AwsSdkCall(  # will also be called for a CREATE event
                service="@aws-sdk/client-bedrock-agent",
                action="associateAgentCollaborator",
                parameters={
                    "agentDescriptor": {"aliasArn": self.alias_arn},
                    "agentId": self.agent_id,
                    "agentVersion": self.agent_version,
                    "collaborationInstruction": self.collaboration_instruction,
                    "collaboratorName": self.collaborator_name,
                    "relayConversationHistory": self.relay_conversation_history,
                },
                physical_resource_id=self.physical_resource_id,
            ),
            on_update=cr.AwsSdkCall(  # will also be called for a CREATE event
                service="@aws-sdk/client-bedrock-agent",
                action="updateAgentCollaborator",
                 parameters={
                    "agentDescriptor": {"aliasArn": self.alias_arn},
                    "agentId": self.agent_id,
                    "agentVersion": self.agent_version,
                    "collaborationInstruction": self.collaboration_instruction,
                    "collaboratorName": self.collaborator_name,
                    "relayConversationHistory": self.relay_conversation_history,
                },
                physical_resource_id=self.physical_resource_id,
            ),
            on_delete=cr.AwsSdkCall(  # will also be called for a CREATE event
                service="@aws-sdk/client-bedrock-agent",
                action="DisassociateAgentCollaborator",
                 parameters={
                    "agentId": self.agent_id,
                    "agentVersion": self.agent_version,
                    "collaboratorId": self.collaborator_id,
                },
                physical_resource_id=self.physical_resource_id,
            ) if self.collaborator_id else None,
            
            install_latest_aws_sdk=True,
            policy=cr.AwsCustomResourcePolicy.from_statements(
                [
                    iam.PolicyStatement(
                        actions=["bedrock:AssociateAgentCollaborator", "bedrock:UpdateAgentCollaborator", "bedrock:DisassociateAgentCollaborator"],
                        resources=["arn:aws:bedrock:*:*:agent/*"],
                    )
                ]
            ),
        )

        self.collaborator_id = self.collaboration_cr.get_response_field("agentCollaborator.collaboratorId")
        CfnOutput(self, "collabid", value= self.collaborator_id)