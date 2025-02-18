import json, decimal, os

from whatsapp import send_whatsapp_text
from connections_service import ConnectionsService




def lambda_handler(event, context):
    records = event.get("Records", [])
    connections         = ConnectionsService(os.environ.get("TABLE_NAME"))

    for record in records:
        sns = record.get("Sns", {})
        sns_message_str = sns.get("Message", "{}")
        message = json.loads(sns_message_str, parse_float=decimal.Decimal)

        print("Message")
        print(message)
        message_type= message['Type']
        
        if(message_type == 'MESSAGE'):
            message_attributes = record['Sns']['MessageAttributes']
            message_body = message['Content']
            contactId = message['ContactId']

            ParticipantRole = message['ParticipantRole']
            MessageVisibility = message_attributes['MessageVisibility']['Value']
            if((MessageVisibility == 'CUSTOMER' or MessageVisibility == 'ALL')  and ParticipantRole != 'CUSTOMER' ):
                print("contactId:" + str(contactId))
                customer = connections.get_customer(contactId)
                if(customer):
                    phone = customer['customerId']
                    systemNumber = customer['systemNumber']
                    send_whatsapp_text(message_body,phone, systemNumber)
                else:
                    print('Contact not found')
                print('Contact not found')
        
        if(message_type == 'EVENT'):
            message_attributes = record['Sns']['MessageAttributes']
            message_type = message_attributes['ContentType']['Value']
            if(message_type == 'application/vnd.amazonaws.connect.event.participant.left' or message_type == 'application/vnd.amazonaws.connect.event.chat.ended'):
                print('participant left')
                contactId = message['InitialContactId']
                # connections.remove_contactId(contactId) # Optional

            