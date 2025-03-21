def parse_parameters(parameters):
    parsed_parameters = {}
    for param in parameters:
        parsed_parameters[param["name"]] = param["value"]
    return parsed_parameters


def parse_event(event):
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


class AgentHelper:
    def __init__(self, event) -> None:
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
        action_response = {
            "actionGroup": self.actionGroup,
            "function": self.function,
            "functionResponse": {"responseBody": {"TEXT": {"body": message}}},
        }
        function_response = {'response': action_response, 'messageVersion': self.messageVersion}

        return function_response
