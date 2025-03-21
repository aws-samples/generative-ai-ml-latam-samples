import boto3
import json
import os
import boto3.dynamodb
import boto3.dynamodb.table


BUCKET_NAME = os.environ.get("BUCKET_NAME")
VOICE_PREFIX = os.environ.get("VOICE_PREFIX", "voice_")
ATTACHMENT_PREFIX = os.environ.get("ATTACHMENT_PREFIX", "attachment_")
META_API_VERSION = "v21.0"


class WhatsappMessage:
    def __init__(
        self,
        meta_phone_number,
        message,
        metadata={},
        client=None,
        meta_api_version=META_API_VERSION,
        download_attachments = True
    ) -> None:
        # arn:aws:social-messaging:region:account:phone-number-id/976c72a700aac43eaf573ae050example
        self.meta_phone_number = meta_phone_number
        self.phone_number_arn = meta_phone_number.get("arn", "")
        # phone-number-id-976c72a700aac43eaf573ae050example
        self.phone_number_id = self.phone_number_arn.split(":")[-1].replace("/", "-")
        self.message = message
        self.metadata = metadata
        self.phone_number = message.get("from", "")
        self.meta_api_version = meta_api_version
        self.message_id = message.get("id", "")
        self.client = client if client else boto3.client("socialmessaging")
        self.s3_client = boto3.client("s3")
        self.attachment = None
        self.transcription = None
        self.get_attachment(download=download_attachments)

    def add_transcription(self, transcription):
        self.transcription = transcription
        self.message["audio"].update({"transcription": transcription})

    def get_text(self):
        if self.attachment:
            return self.attachment.get("caption", "")
        else:
            return self.message.get("text", {}).get("body", "")

    def get_audio(self, download=True):
        audio = self.message.get("audio", None)

        if not audio:
            return {}
        if not download:
            return audio

        media_id = audio.get("id")

        media_content = self.download_media(
            media_id=media_id,
            phone_id=self.phone_number_id,
            bucket_name=BUCKET_NAME,
            media_prefix=ATTACHMENT_PREFIX,
        )

        # print("media content:", media_content)
        # update self.message.audio with media_content
        del media_content["ResponseMetadata"]
        audio.update(media_content)

        # update self.message with audio
        self.message.update({"audio": audio})
        return audio

    def get_attachment(self, download=True):
        # Check for audio, image, document, video, or other attachment types
        print("getting attachement for message:", self.message)
        attachment = None
        if self.message.get("audio"):
            attachment = self.message.get("audio")
            attachment_type = "audio"
        if self.message.get("image"):
            attachment = self.message.get("image")
            attachment_type = "image"
        elif self.message.get("document"):
            attachment = self.message.get("document")
            attachment_type = "document"
        elif self.message.get("video"):
            attachment = self.message.get("video")
            attachment_type = "video"
        elif self.message.get("sticker"):
            attachment = self.message.get("sticker")
            attachment_type = "sticker"

        if not attachment:
            return {}

        print("Attachment Found:", attachment)

        if not download:
            return attachment

        media_id = attachment.get("id")

        media_content = self.download_media(
            media_id=media_id,
            phone_id=self.phone_number_id,
            bucket_name=BUCKET_NAME,
            media_prefix=ATTACHMENT_PREFIX,
        )

        # Update attachment with media content
        if "ResponseMetadata" in media_content:
            del media_content["ResponseMetadata"]

        attachment.update(media_content)
        print("Attachment Saved:", attachment)

        binary = self.get_s3_file_content(media_content.get("location"))
        attachment.update({"content": binary})

        print("binary OK")

        # Update message with attachment
        self.message.update({attachment_type: attachment})
        self.attachment = attachment

    # https://docs.aws.amazon.com/social-messaging/latest/userguide/receive-message-image.html
    def download_media(self, media_id, phone_id, bucket_name, media_prefix):
        media_content = self.client.get_whatsapp_message_media(
            mediaId=media_id,
            originationPhoneNumberId=phone_id,
            destinationS3File={"bucketName": bucket_name, "key": media_prefix},
        )
        extension = media_content.get("mimeType", "").split("/")[-1]
        # print("media content:", media_content)
        return dict(
            **media_content,
            location=f"s3://{bucket_name}/{media_prefix}{media_id}.{extension}",
        )

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
        # print(kwargs)
        response = self.client.send_whatsapp_message(**kwargs)
        print("replied to message:", response)
        # message_object["id"] = response.get("messageId")
        # message_object["from"] = self.phone_number
        # replied_message = WhatsappMessage(self.meta_phone_number, message_object , self.metadata)
        # return replied_message

    def save(self, table):
        print("saving message...")
        table.put_item(Item=dict(**self.message, **self.metadata))

    def get_s3_file_content(self, s3_location):
        """
        Download file contents from an S3 location

        Args:
            s3_location (str): S3 URI in the format 's3://bucket-name/key'

        Returns:
            bytes: The content of the S3 file

        Raises:
            ValueError: If the S3 location format is invalid
            Exception: If there's an error downloading the file
        """
        try:
            # Parse the S3 URI
            if not s3_location.startswith("s3://"):
                raise ValueError(
                    "Invalid S3 location format. Expected 's3://bucket-name/key'"
                )

            # Remove 's3://' prefix and split into bucket and key
            path_parts = s3_location[5:].split("/", 1)
            if len(path_parts) != 2:
                raise ValueError(
                    "Invalid S3 location format. Expected 's3://bucket-name/key'"
                )

            bucket_name = path_parts[0]
            object_key = path_parts[1]

            # Get the object from S3
            response = self.s3_client.get_object(Bucket=bucket_name, Key=object_key)

            # Read the content
            content = response["Body"].read()
            return content

        except Exception as e:
            print(f"Error downloading file from S3: {str(e)}")
            raise


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
            # print(f"field:{field}")
            if field == "messages":
                metadata = value.get("metadata", {})
                contacts = value.get("contacts", [])
                phone_number_id = metadata.get("phone_number_id", "")
                phone_number = self.get_phone_number_arn(phone_number_id)
                for message in value.get("messages", []):
                    from_number = message.get("from", "")
                    message.update({"customer_name": self.get_customer_name(from_number, contacts)})
                    print(f"message: {message}")
                    wspm = WhatsappMessage(phone_number, message, metadata)
                    self.messages.append(wspm)
            else:
                print(f"{value}")

    def get_phone_number_arn(self, phone_number_id):
        for phone_number in self.meta_phone_number_ids:
            if phone_number.get("metaPhoneNumberId") == phone_number_id:
                return phone_number

    def get_customer_name(self, from_number, contacts  ):
        for contact in contacts:
            if contact.get("wa_id") == from_number:
                return contact.get("profile", {}).get("name", "NN")
        return ""

