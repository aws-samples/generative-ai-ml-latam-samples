import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class BedrockAgentService:
    def __init__(self, agent_id, alias_id="TSTALIASID", client=None) -> None:
        self.agents_runtime_client = (
            client if client else boto3.client("bedrock-agent-runtime")
        )
        self.agent_id = agent_id
        self.alias_id = alias_id

    def get_session(self, session_id):
        return self.agents_runtime_client.get_session(sessionIdentifier=session_id)

    def list_sessions(self):
        return self.agents_runtime_client.list_sessions(maxResults=20).get(
            "sessionSummaries"
        )

    def get_agent_memory(self, memory_id):
        return self.agents_runtime_client.get_agent_memory(
            agentId=self.agent_id,
            agentAliasId=self.alias_id,
            maxItems=100,
            memoryId=memory_id,
            memoryType="SESSION_SUMMARY",
        ).get("memoryContents")

    def invoke_agent(self, prompt, session_id, memory_id, session_attributes=None):
        try:
            invocation_kwargs = dict(
                agentId=self.agent_id,
                agentAliasId=self.alias_id,
                sessionId=session_id,
                memoryId=memory_id,
                inputText=prompt,
            )
            if session_attributes:
                invocation_kwargs["sessionState"] = {
                    "sessionAttributes": session_attributes
                }

            print(f"Invocando Agente: {invocation_kwargs}")

            response = self.agents_runtime_client.invoke_agent(**invocation_kwargs)

            print(
                f"Response: memoryId = {response.get('memoryId')} / sessionId =  {response.get('sessionId')}"
            )

            completion = ""

            for event in response.get("completion"):
                chunk = event["chunk"]
                completion = completion + chunk["bytes"].decode()

        except ClientError as e:
            logger.error(f"Couldn't invoke agent. {e}")
            raise

        return completion
