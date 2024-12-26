import boto3
import json
import os
import boto3.dynamodb
import boto3.dynamodb.table




class WhatsappMessage:
    def __init__(
        self, meta_phone_number, message, metadata = {}, client=None, meta_api_version="v20.0"
    ) -> None:
        # arn:aws:social-messaging:region:account:phone-number-id/976c72a700aac43eaf573ae050example
        self.phone_number_arn = meta_phone_number.get("arn", "")
        # phone-number-id-976c72a700aac43eaf573ae050example
        self.phone_number_id = self.phone_number_arn.split(":")[-1].replace("/", "-")
        self.message = message
        self.metadata = metadata
        self.phone_number = message.get("from", "")
        self.meta_api_version = meta_api_version
        self.message_id = message.get("id", "")
        self.client = client if client else boto3.client("socialmessaging")

    def get_text(self):
        return self.message.get("text", {}).get("body", "")

    def mark_as_read(self):
        message_object = {
            "messaging_product": "whatsapp",
            "message_id": self.message_id,
            "status": "read",
        }

        kwargs = dict(
            originationPhoneNumberId=self.phone_number_arn,
            metaApiVersion=self.meta_api_version,
            message=bytes(json.dumps(message_object), "utf-8"),
        )
        # print (kwargs)
        response = self.client.send_whatsapp_message(**kwargs)
        print("mark as read:", response)

    def reaction(self, emoji):
        message_object = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": f"+{self.phone_number}",
            "type": "reaction",
            "reaction": {"message_id": self.message_id, "emoji": emoji},
        }

        kwargs = dict(
            originationPhoneNumberId=self.phone_number_arn,
            metaApiVersion=self.meta_api_version,
            message=bytes(json.dumps(message_object), "utf-8"),
        )
        # print(kwargs)
        response = self.client.send_whatsapp_message(**kwargs)
        print("react to message:", response)

    def text_reply(self, text_message):
        print("reply message...")
        message_object = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "context": {"message_id": self.message_id},
            "to": f"+{self.phone_number}",
            "type": "text",
            "text": {"preview_url": False, "body": text_message},
        }

        kwargs = dict(
            originationPhoneNumberId=self.phone_number_id,
            metaApiVersion=self.meta_api_version,
            message=bytes(json.dumps(message_object), "utf-8"),
        )
        print(kwargs)
        response = self.client.send_whatsapp_message(**kwargs)
        print("react to message:", response)

    def save(self,table):
        print("saving message...")
        table.put_item(Item=dict(**self.message, **self.metadata))
    
class WhatsappService:
    def __init__(self, sns_message) -> None:
        self.context = sns_message.get("context", {})
        self.meta_phone_number_ids = self.context.get("MetaPhoneNumberIds", [])
        self.meta_waba_ids = self.context.get("MetaWabaIds", [])
        self.webhook_entry = json.loads(sns_message.get("whatsAppWebhookEntry", {}))
        self.message_timestamp = sns_message.get("message_timestamp", "")
        self.changes = self.webhook_entry.get("changes", [])
        self.messages = []

        for change in self.changes:
            value = change.get("value", {})
            field = change.get("field", "")
            print(f"field:{field}")
            if field == "messages":
                metadata = value.get("metadata", {})
                phone_number_id = metadata.get("phone_number_id", "")
                phone_number = self.get_phone_number_arn(phone_number_id)
                for message in value.get("messages", []):
                    self.messages.append(WhatsappMessage(phone_number, message, metadata))
            else:
                print(f"{value}")

    def get_phone_number_arn(self, phone_number_id):
        for phone_number in self.meta_phone_number_ids:
            if phone_number.get("metaPhoneNumberId") == phone_number_id:
                return phone_number
            