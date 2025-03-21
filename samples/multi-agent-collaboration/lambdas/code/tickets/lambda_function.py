import json
from ticket_service import TicketService
from agent_helpers import AgentHelper


def lambda_handler(event, context):
    """
    Lambda function handler for processing ticket-related agent requests.
    
    Args:
        event: The event from the agent containing request details
        context: Lambda context object
        
    Returns:
        Dict containing the formatted agent response
    """
    print("Received event: ")
    print(event)
    agent_helper = AgentHelper(event)
    rut = agent_helper.parameters.get("identity_document_number") 
    order_number = agent_helper.parameters.get("order_number")
    description = agent_helper.parameters.get("description")
    ticket_number = agent_helper.parameters.get("ticket_number")
    sessionId = agent_helper.sessionId

    function_response = agent_helper.response("Unknown error")

    if agent_helper.function == "cutTicket":
        if rut is None:
            function_response = agent_helper.response("rut not provided")
            
        if order_number is None:
            function_response = agent_helper.response("order number not provided")

        if description is None:
            function_response = agent_helper.response("description not provided")

        if (rut and order_number and description):
            ticket_service = TicketService(order_number=order_number)
            response = ticket_service.cut_ticket(sessionId, rut, description)
            function_response = agent_helper.response(response)

    elif agent_helper.function == "getTicket":
        if ticket_number is None:
            function_response = agent_helper.response("ticket number not provided")

        if ticket_number:
            ticket_service = TicketService(order_number=order_number)
            response = ticket_service.get_ticket(ticket_number)
            function_response = agent_helper.response(json.dumps(response))

    else:
        function_response = agent_helper.response(f"Unknown function: {agent_helper.function}")

    print(f"Response: {function_response}") 
    return function_response

