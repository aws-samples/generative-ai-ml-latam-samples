import os


from connect_chat_service import ChatService
from connections_service import ConnectionsService


def lambda_handler(event, context):
    chat = ChatService(
        instance_id=os.environ.get("INSTANCE_ID"),
        topic_arn=os.environ.get("TOPIC_ARN"))
    
    connections         = ConnectionsService(os.environ.get("TABLE_NAME"))

    print("Starting request", {"event": event})
    
    contact_id = event.get('Details', {}).get('ContactData', {}).get('ContactId')
    status = "failure"
    
    # Create participant
    participant_detail = chat.create_participant(contact_id)
    
    if (participant_detail and 
        participant_detail.get('ParticipantId') and 
        participant_detail.get('ParticipantCredentials', {}).get('ParticipantToken')):
        
        # Start chat streaming
        streaming_id = chat.start_stream(contact_id)
        
        # Create participant connection
        participant_connection = chat.create_participant_connection(
            participant_detail['ParticipantCredentials']['ParticipantToken']
        )
        
        if (participant_connection and 
            participant_connection.get('ConnectionCredentials', {}).get('ConnectionToken') and 
            streaming_id):
            
            status = "success"
            
            # Store results
            connections.save_chat_contact_details(
                contact_id,
                participant_connection['ConnectionCredentials']['ConnectionToken'],
                streaming_id
            )
            
            # Send initial message
            chat.send_message(
                participant_connection['ConnectionCredentials']['ConnectionToken'],
                'I\'m an automated assistant. Ask me questions or reply "quit" to exit.'
            )

    
    
    response = {"status": status}
    print("Ending response", {"response": response})
    return response


