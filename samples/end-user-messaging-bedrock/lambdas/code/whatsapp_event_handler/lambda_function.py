import json, decimal
import boto3
import os

from whatsapp import WhatsappService
from bedrock_agent import BedrockAgentService
from transcribe import TranscribeService

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME")
table = dynamodb.Table(TABLE_NAME)


AGENT_ID = os.environ.get("AGENT_ID")
AGENT_ALIAS_ID = os.environ.get("AGENT_ALIAS_ID")


def process_record(record):
    sns = record.get("Sns", {})
    sns_message_str = sns.get("Message", "{}")
    sns_message = json.loads(sns_message_str, parse_float=decimal.Decimal)
    whatsapp = WhatsappService(sns_message)
    bedrock_agent = BedrockAgentService(AGENT_ID, AGENT_ALIAS_ID)
    transcribe_service = TranscribeService()

    for message in whatsapp.messages:
        audio = message.get_audio(download = True) # Check if there is audio
        transcription = None
        
        if audio.get("location"): # it's been downloaded
            print ("TRANSCRIBE IT")
            transcription = transcribe_service.transcribe(audio.get("location"))
            message.add_transcription(transcription)

        message.save(table)
        message.mark_as_read()
        message.reaction("👍")


        
        if transcription:
            message.text_reply(f"🔊_{transcription}_")
            response = bedrock_agent.invoke_agent(message.phone_number, transcription)
            print(f"agent response: {response}")
            message.text_reply(response)
            continue

        text = message.get_text()
        
        if text.startswith("/echo "):            
            message.text_reply(text.replace("/echo ", ""))
            continue
        
        print(f"query: {text}")
        response = bedrock_agent.invoke_agent(message.phone_number, text)
        print(f"agent response: {response}")
        message.text_reply(response)




def lambda_handler(event, context):
    records = event.get("Records", [])
    #print (f"processing {len(records)} records")
    for rec in records:
        process_record(rec)
