from constructs import Construct
from bedrock_agent.create_role import CreateAgentRole
from aws_cdk import (
    custom_resources as cr,
    aws_iam as iam,
    aws_bedrock as bedrock,
    RemovalPolicy,
)

AGENT_REMOVAL_POLICY = RemovalPolicy.DESTROY


def build_agent_collaborator_property(agent, instruction, name, relay_conversation=True):
    """
    Builds collaboration properties for an agent.
    
    Args:
        agent: The agent to build properties for
        instruction: Instructions for the agent collaboration
        name: Name of the collaborator
        relay_conversation: Whether to relay conversations
        
    Returns:
        Dictionary containing collaboration properties
    """
    agent_collaborator_property = bedrock.CfnAgent.AgentCollaboratorProperty(
        agent_descriptor=bedrock.CfnAgent.AgentDescriptorProperty(
            alias_arn=agent.cfn_alias.attr_agent_alias_arn
        ),
        collaboration_instruction=instruction,
        collaborator_name=name,
        # the properties below are optional
        relay_conversation_history="TO_COLLABORATOR" if relay_conversation else "DISABLED",
    )
    return agent_collaborator_property


"""
Class representing an Amazon Bedrock Agent with collaboration capabilities.
"""
class Agent(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        action_groups,
        agent_name,
        agent_description,
        foundation_model,
        agent_instruction,
        agent_collaboration="DISABLED",
        collaborators=[],
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Agent Execution Role
        self.agent_role = CreateAgentRole(self, "role", base_name=agent_name)
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.agent_instruction = agent_instruction
        self.foundation_model = foundation_model
        self.agent_collaboration = agent_collaboration
        self.agents_collaborators = collaborators

        agent_kwags = dict(
            agent_name=self.agent_name,
            description=self.agent_description,
            auto_prepare=True,
            idle_session_ttl_in_seconds=600,
            skip_resource_in_use_check_on_delete=True,
            test_alias_tags={"test_alias_tags_key": "testAliasTags"},
            agent_resource_role_arn=self.agent_role.service_role.role_arn,
            instruction=self.agent_instruction,
            foundation_model=self.foundation_model,
        )

        if action_groups:
            agent_kwags["action_groups"] = action_groups

        if len(self.agents_collaborators):
            agent_kwags["agent_collaboration"] = self.agent_collaboration
            agent_kwags["agent_collaborators"] = self.agents_collaborators

        self.cfn_agent = bedrock.CfnAgent(self, "Agent", **agent_kwags)
        self.cfn_agent.apply_removal_policy(AGENT_REMOVAL_POLICY)
        self.cfn_agent.node.add_dependency(self.agent_role.service_role)

    def create_alias(self, alias_name):
        self.cfn_alias = bedrock.CfnAgentAlias(
            self,
            "AgentAlias",
            agent_id=self.cfn_agent.attr_agent_id,
            agent_alias_name=alias_name,
        )
        return self.cfn_alias
