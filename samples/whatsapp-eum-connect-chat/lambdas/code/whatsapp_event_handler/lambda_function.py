import json, decimal
import boto3
import os

from whatsapp import WhatsappService
from transcribe import TranscribeService
from connections_service import ConnectionsService
from connect_chat_service import ChatService





def lambda_handler(event, context):
    records             = event.get("Records", [])
    transcribe_service  = TranscribeService()
    connections         = ConnectionsService(os.environ.get("TABLE_NAME"))
    chat                = ChatService(
                            instance_id=os.environ.get("INSTANCE_ID"),
                            contact_flow_id=os.environ.get("CONTACT_FLOW_ID"),
                            chat_duration_minutes=int(os.environ.get("CHAT_DURATION_MINUTES", 60)),
                            topic_arn=os.environ.get("TOPIC_ARN")
                            )

    for record in records:
        sns = record.get("Sns", {})
        sns_message_str = sns.get("Message", "{}")
        sns_message = json.loads(sns_message_str, parse_float=decimal.Decimal)
        print(f"processing message: {sns_message}")
        whatsapp = WhatsappService(sns_message)
        
        for message in whatsapp.messages:
            audio = message.get_audio(download=True)  # Check if there is audio
            transcription = None

            if audio.get("location"):  # it's been downloaded
                print("TRANSCRIBE IT")
                transcription = transcribe_service.transcribe(audio.get("location"))
                message.add_transcription(transcription)

            contact = connections.get_contact(message.phone_number)

            text = message.get_text()

            if transcription:
                message.text_reply(f"🔊_{transcription}_")
                text =  transcription

            if not text:
                print ("No hay Texto")
                return


            customer_name = "NN" 

            if(contact):
                print(f"Found existing connection for {message.phone_number}")

                try:
                    send_message_response = chat.send_message(text, message.phone_number, contact['connectionToken'])
                except:
                    print('Invalid Connection Token')
                    connections.remove_contactId(contact['contactId'])
                    print('Initiating connection')  
                    contactId, participantToken, connectionToken = chat.start_chat_and_stream(
                        text, message.phone_number, "Whatsapp", customer_name, message.phone_number_id)
                    
                    connections.update_contact(
                        message.phone_number, "Whatsapp", contactId, participantToken, connectionToken, customer_name, 
                        message.phone_number_id)
                    
            #Contacto No existe!
            else:
                print("Creating new contact")
                contactId, participantToken, connectionToken = chat.start_chat_and_stream(
                        text, message.phone_number, "Whatsapp", customer_name, message.phone_number_id)
                
                connections.insert_contact(message.phone_number, "Whatsapp", contactId, participantToken, connectionToken, customer_name, 
                        message.phone_number_id)
