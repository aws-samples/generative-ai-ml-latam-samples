import boto3
import json

socialessaging = boto3.client("socialmessaging")

META_API_VERSION = "v21.0"


def get_file_category(mime_type):
    # Map MIME types to WhatsApp file categories
    if mime_type.startswith("image/"):
        return "image"
    elif mime_type.startswith("video/"):
        return "video"
    elif mime_type.startswith("audio/"):
        return "audio"
    elif mime_type in [
        "application/pdf",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]:
        return "document"
    else:
        # Default to document for unknown types
        return "document"


def send_whatsapp_text(
    text_message, to, phone_number_id, meta_api_version=META_API_VERSION
):
    print("sending message...")
    message_object = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": f"+{to}",
        "type": "text",
        "text": {"preview_url": False, "body": text_message},
    }

    kwargs = dict(
        originationPhoneNumberId=phone_number_id,
        metaApiVersion=meta_api_version,
        message=bytes(json.dumps(message_object), "utf-8"),
    )
    # print(kwargs)
    response = socialessaging.send_whatsapp_message(**kwargs)
    print("replied to message:", response)


def send_whatsapp_attachment(
    attachment_url,
    mime_type,
    name,
    to,
    phone_number_id,
    meta_api_version=META_API_VERSION,
):
    print("sending attachment...")
    message_type = get_file_category(mime_type)
    message_object = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": f"+{to}",
        "type": message_type,
    }
    message_object[message_type] = {"link": attachment_url}
    if message_type == "document":
        message_object[message_type]["filename"] = name

    kwargs = dict(
        originationPhoneNumberId=phone_number_id,
        metaApiVersion=meta_api_version,
        message=bytes(json.dumps(message_object), "utf-8"),
    )
    # print(kwargs)
    response = socialessaging.send_whatsapp_message(**kwargs)
    print("attachment response:", response)
