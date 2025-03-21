import json
import os
import time
from connect_chat_service import ChatService
from connections_service import ConnectionsService
from bedrock_agent import BedrockAgentService

connections_service = ConnectionsService(os.environ.get("TABLE_NAME"))


def handle_quit_command(chat_service):
    """Handle the quit command from the user."""
    chat_service.disconnect()
    chat_service.stop_chat_streaming()
    return True


def update_chat_service(chat_service, contact_id, conection_token, straming_id):
    chat_service.set_connection_token(conection_token)
    chat_service.set_contact_id(contact_id)
    chat_service.set_streaming_id(straming_id)

def process_message(message_object):
    print("Message", message_object)

    contact_id = message_object.get("ContactId")
    content = message_object.get("Content")

    if not (contact_id and content):
        print("Invalid message")
        return
    
    chat_contact = connections_service.get_chat_contact(contact_id)
    connection_token = chat_contact.get("connectionToken")
    # print("Chat Contact", chat_contact)

    if not(chat_contact and connection_token):
        print(f"No connection token found {message_object['ContactId']}")
        return


    chat_service = ChatService(instance_id=os.environ.get("INSTANCE_ID"))
    update_chat_service(chat_service, contact_id, connection_token, chat_contact["streamingId"])

    bedrock_agent = BedrockAgentService( os.environ.get("AGENT_ID"), os.environ.get("AGENT_ALIAS_ID"), contact_id)



    if content.lower() == "quit": return handle_quit_command(chat_service)

    # Answer with Agent
    chat_service.send_typing_event()
    response = bedrock_agent.invoke_agent(content)
    print (f"Response: {response}")

    if type(response) == str: 
        chat_service.send_message(response or "error generating answer")

    elif type(response) == dict:
        print("Updating Contact Attributes")
        chat_service.update_contact_attributes(attributes =response)
        chat_service.send_message( f"Action: {response.get('functionName')}")


        # Dummy response from fictional system invocation_result = OK
        return_control_response = bedrock_agent.return_control_invocation_results(
                invocation_id=response.get("invocationId"),
                action_group=response.get("actionGroup"),
                function_name=response.get("functionName"),
                invocation_result="OK",
                agent_id = response.get("agentId")
            )
        chat_service.disconnect()
        print(f"return_control_response: {return_control_response}")
        




def lambda_handler(event: dict, context) -> dict:
    """
    AWS Lambda handler for processing SNS messages related to chat interactions.

    This function processes incoming chat messages, manages chat connections, and coordinates
    responses between users and the Bedrock agent. It handles message routing, typing indicators,
    and special commands like 'quit'.

    Args:
        event (dict): The Lambda event containing SNS message records
        context: The Lambda context object

    Returns:
        dict: Response indicating success/failure of message processing
    """

    for record in event["Records"]:
        message_object = json.loads(record["Sns"]["Message"])
        process_message(message_object)