import boto3
import os
import sys
from botocore.exceptions import ClientError

participant_client = boto3.client("connectparticipant")
connect_client = boto3.client("connect")


class ChatService:
    def __init__(
        self,
        instance_id=os.environ.get("INSTANCE_ID"),
        contact_flow_id=os.environ.get("CONTACT_FLOW_ID"),
        chat_duration_minutes=60,
        topic_arn = os.environ.get("TOPIC_ARN")
    ) -> None:
        self.participant = boto3.client("connectparticipant")
        self.connect = boto3.client("connect")
        self.contact_flow_id = contact_flow_id
        self.instance_id = instance_id
        self.chat_duration_minutes = chat_duration_minutes
        self.topic_arn = topic_arn

    def start_chat(
        self, message, phone, channel, name="unknown", systemNumber="unknown"
    ):

        start_chat_response = self.connect.start_chat_contact(
            InstanceId=self.instance_id,
            ContactFlowId=self.contact_flow_id,
            Attributes={
                "Channel": channel,
                "customerId": phone,
                "customerName": name,
                "systemNumber": systemNumber,
            },
            ParticipantDetails={"DisplayName": phone},
            InitialMessage={"ContentType": "text/plain", "Content": message},
            ChatDurationInMinutes=self.chat_duration_minutes,
            SupportedMessagingContentTypes=[
                "text/plain",
                "text/markdown",
                "application/json",
                "application/vnd.amazonaws.connect.message.interactive",
                "application/vnd.amazonaws.connect.message.interactive.response",
            ],
        )
        print (start_chat_response)
        return start_chat_response

    def send_message(self, message, connectionToken):
        response = self.participant.send_message(
            ContentType="text/plain", Content=message, ConnectionToken=connectionToken
        )
        return response

    def start_stream(self, ContactId):
        if not self.topic_arn:
            print ("Missing Topic ARN for start streamming")
            return None

        start_stream_response = connect_client.start_contact_streaming(
            InstanceId=self.instance_id,
            ContactId=ContactId,
            ChatStreamingConfiguration={"StreamingEndpointArn": self.topic_arn})
        
        return start_stream_response

    def start_chat_and_stream( self, message, phone, channel, name="unknown", systemNumber="unknown"):
        start_chat_response         = self.start_chat(message, phone, channel, name, systemNumber)

    
        participantToken             = start_chat_response["ParticipantToken"]
        contactId                   = start_chat_response['ContactId']
        
        start_stream_response       = self.start_stream(contactId)
        create_connection_response  = self.create_connection(participantToken)
        connectionToken             = create_connection_response['ConnectionCredentials']['ConnectionToken']

        return contactId, participantToken, connectionToken


    def create_connection(self, ParticipantToken):

        create_connection_response = self.participant.create_participant_connection(
            Type=["CONNECTION_CREDENTIALS"],
            ParticipantToken=ParticipantToken,
            ConnectParticipant=True
        )
        return create_connection_response

    def get_signed_url(self, connectionToken, attachment):
        try:
            response = self.participant.get_attachment(
                AttachmentId=attachment, ConnectionToken=connectionToken
            )
        except ClientError as e:
            print("Get attachment failed")
            print(e.response["Error"]["Code"])
            return None
        else:
            return response["Url"]


    def attach_file(self, fileContents, fileName, fileType, ConnectionToken):
        # Method to attach a file to the chat
        # Parameters:
        #   fileContents: Contents of the file to attach
        #   fileName: Name of the file
        #   fileType: MIME type of the file
        #   ConnectionToken: Token for the chat connection
        # Returns: None
        # Raises: NotImplementedError
        raise NotImplementedError("File attachment functionality not yet implemented")
