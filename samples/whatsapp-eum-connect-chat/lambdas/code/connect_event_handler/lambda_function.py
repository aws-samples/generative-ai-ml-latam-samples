import json, decimal, os

from whatsapp import send_whatsapp_text, send_whatsapp_attachment
from connections_service import ConnectionsService, get_signed_url


connections         = ConnectionsService(os.environ.get("TABLE_NAME"))


def process_message(message_attributes, message):
    message_body = message['Content']
    contactId = message['ContactId']

    MessageVisibility = message_attributes['MessageVisibility']['Value']
    if((MessageVisibility == 'CUSTOMER' or MessageVisibility == 'ALL')):
        print("contactId:" + str(contactId))
        customer = connections.get_customer(contactId)
        if(customer):
            phone = customer['customerId']
            systemNumber = customer['systemNumber']
            send_whatsapp_text(message_body,phone, systemNumber)
        else:
            print('Contact not found')
        print('Contact not found')

def process_event(message_attributes, message):
    message_type = message_attributes['ContentType']['Value']
    if(message_type == 'application/vnd.amazonaws.connect.event.participant.left' or message_type == 'application/vnd.amazonaws.connect.event.chat.ended'):
        print('participant left')
        contactId = message['InitialContactId']
        # connections.remove_contactId(contactId) # Optional
    
def process_attachment(message_attributes, message):
    contactId = message['ContactId']
    customer = connections.get_customer(contactId)
    
    if customer:
        phone = customer['customerId']
        systemNumber = customer['systemNumber']
        connectionToken = customer['connectionToken']
        
        # Process attachments
        attachments = message.get('Attachments', [])
        for attachment in attachments:
            if attachment['Status'] == 'APPROVED':
                attachment_id = attachment['AttachmentId']
                attachment_name = attachment['AttachmentName']
                content_type = attachment['ContentType']
                
                # Get signed URL for the attachment
                signed_url = get_signed_url(connectionToken, attachment_id)
            
                send_whatsapp_attachment(signed_url, content_type, attachment_name, phone, systemNumber)
    else:
        print('Contact not found for attachment handling')
        

def process_record(record):
    # Process each record here
    print("Processing record:", record)

    sns = record.get("Sns", {})
    sns_message_str = sns.get("Message", "{}")
    message_attributes = sns.get('MessageAttributes')
    message = json.loads(sns_message_str, parse_float=decimal.Decimal)

    print(f"Message: {message}")
    message_type= message.get('Type')
    ParticipantRole = message.get('ParticipantRole')
    if ParticipantRole == "CUSTOMER":
        print ("ParticipantRole is CUSTOMER, ignoring")
        return



    if(message_type == 'MESSAGE'):
        process_message(message_attributes, message)
    
    if(message_type == 'EVENT'):
        process_event(message_attributes, message)

    if(message_type == 'ATTACHMENT'):
        process_attachment(message_attributes, message)




def lambda_handler(event, context):
    records = event.get("Records", [])

    for record in records:
        process_record(record)