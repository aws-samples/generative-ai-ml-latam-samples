import json

from order_service import OrderService
from agent_helpers import AgentHelper


def lambda_handler(event, context):
    print("Received event: ")
    print(event)
    agent_helper = AgentHelper(event)
    rut = agent_helper.parameters.get("identity_document_number") 
    order_number = agent_helper.parameters.get("order_number")

    function_response = agent_helper.response("Unknown error")

    if agent_helper.function == "getOrderStatus":
        if order_number is None:
            function_response = agent_helper.response("order number not provided")

        if rut is None:
            function_response = agent_helper.response("rut not provided")

        if (rut and order_number ):
            order_service = OrderService()
            response = order_service.get_order(order_number, rut)
            function_response = agent_helper.response(json.dumps(response))
    else:
        function_response = agent_helper.response(f"Unknown function: {agent_helper.function}")

    print(f"Response: {function_response}") 
    return function_response

