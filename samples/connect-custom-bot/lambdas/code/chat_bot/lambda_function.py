import json
import os
import time
from connect_chat_service import ChatService
from connections_service import ConnectionsService



def lambda_handler(event, context):
    chat_service = ChatService( instance_id=os.environ.get("INSTANCE_ID"))
    connections_service = ConnectionsService(os.environ.get("TABLE_NAME"))
    """Handle SNS messages for chat interactions"""
    for record in event['Records']:
        message_object = json.loads(record['Sns']['Message'])
        print("Message", message_object)

        if message_object.get('ContactId') and message_object.get('Content'):
            chat_contact = connections_service.get_chat_contact(message_object['ContactId'])

            if chat_contact and chat_contact.get('connectionToken'):
                if message_object['Content'].lower() == 'quit':
                    chat_service.disconnect(chat_contact['connectionToken'])
                    chat_service.stop_chat_streaming(
                        chat_contact['contactId'], 
                        chat_contact['streamingId']
                    )
                else:
                    chat_service.send_event(chat_contact['connectionToken'])
                    response = invoke_service(message_object['Content'])
                    chat_service.send_message(
                        chat_contact['connectionToken'],
                        response or 'error generating answer'
                    )
                    # Usar Esto para actualizar Attributos, si es necesario para desconectar y Escalar
                    # https://docs.aws.amazon.com/connect/latest/APIReference/API_UpdateContactAttributes.html
            else:
                print(f"No connection token found {message_object['ContactId']}")
        else:
            print("Invalid message")

def invoke_service(question: str):
    time.sleep(3)
    return f"Dijiste: {question}"
    
