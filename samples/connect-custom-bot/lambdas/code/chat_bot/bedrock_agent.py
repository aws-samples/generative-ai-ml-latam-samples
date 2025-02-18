import boto3
from botocore.exceptions import ClientError
import time

class BedrockAgentService:
    """
    A service class to interact with AWS Bedrock Agents.
    
    This class provides functionality to invoke Bedrock agents and handle their responses,
    including parameter parsing and control flow management.
    """
    
    def __init__(self, agent_id: str, alias_id: str = "TSTALIASID", session_id = None, client = None) -> None:
        """
        Initialize the BedrockAgentService.
        
        Args:
            agent_id (str): The ID of the Bedrock agent to interact with
            alias_id (str, optional): The alias ID for the agent. Defaults to "TSTALIASID"
            client: The boto3 client for Bedrock runtime. If None, creates a new client
        """
        self.agents_runtime_client = (
            client if client else boto3.client("bedrock-agent-runtime")
        )
        self.agent_id = agent_id
        self.alias_id = alias_id
        self.session_id = session_id or str(int(time.time()))
        

    def set_session_id(self, session_id: str) -> None:
        """
        Set the session ID for the agent.

        Args:
            session_id (str): The session ID to be used for the agent interaction
        """
        self.session_id = session_id

    def parse_parameters(self, parameters: list) -> dict:
        """
        Parse parameters from the agent response into a dictionary format.
        
        Args:
            parameters (list): List of parameter dictionaries containing name and value pairs
            
        Returns:
            dict: Dictionary mapping parameter names to their values
        """
        return {param["name"]: param["value"] for param in parameters}

    def return_control(self, completion: dict) -> dict:
        """
        Process the completion response and extract control flow information.
        
        Args:
            completion (dict): The completion response from the agent containing control information
            
        Returns:
            dict: Processed control information including invocation details and parameters
        """
        rc = completion.get("returnControl", {})
        invocationId = rc.get("invocationId", "")
        invocationInputs = rc.get("invocationInputs",[])

        return_dict = { "invocationId": invocationId}
        #print (f"completion: {completion}")
        
        if len(invocationInputs):
            functionInvocationInput = invocationInputs[0].get("functionInvocationInput", {})
            actionGroup = functionInvocationInput.get("actionGroup", {})
            agentId = functionInvocationInput.get("agentId", None)
            actionInvocationType = functionInvocationInput.get("actionInvocationType", "")
            functionName = functionInvocationInput.get("function", "")
            parameters = functionInvocationInput.get("parameters", {})
            parsed_parameters = self.parse_parameters(parameters)
            return_dict.update(
                {
                    "actionGroup": actionGroup,
                    "agentId": agentId,
                    "functionName": functionName,
                    "parameters": parsed_parameters,
                    "actionInvocationType": actionInvocationType,
                }
            )
        return return_dict

    def return_control_invocation_results(
        self, 
        invocation_id: str, 
        action_group: str, 
        function_name: str, 
        invocation_result: str,
        agent_id : str  = None,
        session_id: str = None, 
    ) -> str:
        """
        Send the results of a function invocation back to the agent.
        
        Args:
            session_id (str): The current session identifier
            invocation_id (str): The ID of the invocation being responded to
            action_group (str): The action group that was invoked
            function_name (str): The name of the function that was called
            invocation_result (str): The result of the function invocation
            
        Returns:
            str: The completion response from the agent after processing the results
        """
        try:
            response = self.agents_runtime_client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.alias_id,
                sessionId=session_id or self.session_id,
                sessionState={
                    "invocationId": invocation_id,
                    "returnControlInvocationResults": [
                        {
                            "functionResult": {
                                "actionGroup": action_group,
                                "agentId": agent_id or self.agent_id,
                                "function": function_name,
                                "responseBody": {"TEXT": {"body": invocation_result}},
                            }
                        }
                    ],
                },
            )

            completion = ""

            for event in response.get("completion"):
                if event.get("returnControl"):
                    return self.return_control(event)
                chunk = event["chunk"]
                completion = completion + chunk["bytes"].decode()

        except ClientError as e:
            print(f"Couldn't invoke agent. {e}")

        return completion

    # from https://docs.aws.amazon.com/code-library/latest/ug/python_3_bedrock-agent-runtime_code_examples.html
    def invoke_agent(self, prompt: str, session_id: str = None) -> dict:
        """
        Invoke the Bedrock agent with a prompt and handle the response.
        
        Args:
            session_id (str): The session identifier for the conversation
            prompt (str): The user's input prompt to send to the agent
            
        Returns:
            dict: The processed response from the agent including any control flow modifications
        """

        kwargs = dict(
            agentId=self.agent_id,
            agentAliasId=self.alias_id,
            sessionId=session_id or self.session_id,
            inputText=prompt
        )
        if prompt.startswith("/new "):            
            kwargs["inputText"] = prompt.replace("/new ", "")
            kwargs["endSession"] = True

        print ("AGENT INVOCATION KWARGS")
        print (kwargs)
        try:
            response = self.agents_runtime_client.invoke_agent(**kwargs, )

            completion = ""

            for event in response.get("completion"):
                if event.get("returnControl"):
                    return self.return_control(event)
                chunk = event["chunk"]
                completion = completion + chunk["bytes"].decode()

        except ClientError as e:
            print(f"Couldn't invoke agent. {e}")
            return None

        return completion
