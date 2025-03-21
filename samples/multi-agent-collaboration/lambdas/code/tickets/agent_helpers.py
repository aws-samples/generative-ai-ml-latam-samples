def parse_parameters(parameters):
    """
    Parse input parameters from agent request.
    
    Args:
        parameters: Raw parameters from agent request
        
    Returns:
        Dict of parsed parameter values
    """
    parsed_parameters = {}
    for param in parameters:
        parsed_parameters[param["name"]] = param["value"]
    return parsed_parameters


def parse_event(event):
    """
    Parse an incoming agent event.
    
    Args:
        event: Raw event from the agent
        
    Returns:
        Tuple containing parsed event components (actionGroup, function, parameters, etc.)
    """
    actionGroup = event["actionGroup"]
    function = event["function"]
    parameters = event.get("parameters", [])
    parsed_parameters = parse_parameters(parameters)
    inputText = event.get("inputText", "")
    sessionId = event.get("sessionId", "")
    sessionAttributes = event.get("sessionAttributes", {})
    promptSessionAttributes = event.get("promptSessionAttributes", {})
    messageVersion = event.get("messageVersion", "")
    return (
        actionGroup,
        function,
        parsed_parameters,
        inputText,
        sessionId,
        sessionAttributes,
        promptSessionAttributes,
        messageVersion,
    )


"""
Helper class for processing agent requests and formatting responses.
"""
class AgentHelper:
    def __init__(self, event) -> None:
        """
        Initialize the agent helper with event data.
        
        Args:
            event: Raw event from the agent to process
        """
        (
            self.actionGroup,
            self.function,
            self.parameters,
            self.inputText,
            self.sessionId,
            self.sessionAttributes,
            self.promptSessionAttributes,
            self.messageVersion
        ) = parse_event(event)

    def response(self, message):
        """
        Format a response message from the agent.
        
        Args:
            message: Message content to format
            
        Returns:
            Dict containing formatted response
        """
        action_response = {
            "actionGroup": self.actionGroup,
            "function": self.function,
            "functionResponse": {"responseBody": {"TEXT": {"body": message}}},
        }
        function_response = {'response': action_response, 'messageVersion': self.messageVersion}

        return function_response
