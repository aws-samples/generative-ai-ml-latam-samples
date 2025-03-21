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

    def set_connection_token(self, connectionToken):
        self.connection_token = connectionToken

    def set_contact_id(self, contactId):
        self.contact_id = contactId


    def set_streaming_id(self, streaming_id):
        self.streaming_id = streaming_id

    def start_chat(
        self, message, phone, channel, name="unknown", systemNumber="unknown"):

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

    def start_stream(self, ContactId):
        if not self.topic_arn:
            print ("Missing Topic ARN for start streamming")
            return None

        try:
            start_stream_response = connect_client.start_contact_streaming(
                InstanceId=self.instance_id,
                ContactId=ContactId,
                ChatStreamingConfiguration={"StreamingEndpointArn": self.topic_arn})
            return start_stream_response

        except ClientError as e:
            print("Create Participant failed")
            print(e.response["Error"]["Code"])
            return None

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

    def create_participant(self, contact_id: str):
        """Create a participant in the chat"""
        command = dict( 
            InstanceId =  self.instance_id,
            ContactId = contact_id,
            ParticipantDetails =  {
                'ParticipantRole': 'CUSTOM_BOT',
                'DisplayName': 'Assistente'
            }
        )
        
        try:
            response = self.connect.create_participant(**command)
            print("Create Participant", {"command": command, "response": response})
            return response
        except ClientError as e:
            print("Create Participant failed")
            print(e.response["Error"]["Code"])
            return None
        
    def create_participant_connection(self, token: str):
        """Create a participant connection"""
        command = dict( Type =  ['CONNECTION_CREDENTIALS'],
            ConnectParticipant = True,
            ParticipantToken = token
        )
        
        try:
            response = self.participant.create_participant_connection(**command)
            print("Create Participant Connection", {"command": command, "response": response})
            return response
        except ClientError as e:
            print("Create Participant Connection failed")
            print(e.response["Error"]["Code"])
            return None

    def send_message(self, message: str, content_type: str = "text/plain"):
        """Send a message in the chat"""

        command = dict(
            ContentType = content_type,
            Content = message,
            ConnectionToken = self.connection_token
        )
        
        try:
            response = self.participant.send_message(**command)
            return response.get('Id')
        except Exception as error:
            print(f"Sending message error: {str(error)}")
            return None

    def send_typing_event(self):
        """Send a typing event in the chat"""
        command = dict(
            ConnectionToken = self.connection_token,
            ContentType = 'application/vnd.amazonaws.connect.event.typing'
        )
        
        try:
            response = self.participant.send_event(**command)
            # print("Sending event", {"command": command, "response": response})
        except Exception as error:
            print(f"Sending event error: {str(error)}")

    def disconnect(self):
        """Disconnect a participant from the chat"""

        try:
            response = self.participant.disconnect_participant(ConnectionToken=self.connection_token)
            print("Disconnecting bot", {"connection_token": self.connection_token, "response": response})
        except Exception as error:
            print(f"Disconnecting bot error: {str(error)}")
            
    def update_contact_attributes(self, contact_id: str = None, attributes: dict = {}):
        """
        Updates the contact attributes for the specified contact.
        
        Args:
            contact_id (str): The identifier of the contact.
            attributes (dict): The attributes to update. Each key-value pair in this dictionary
                             represents an attribute name and its value.
        
        Returns:
            dict: The response from the update_contact_attributes operation.
        """

        formatted_attributes = {
            key: str(value)
            for key, value in attributes.items()
        }
        
        return self.connect.update_contact_attributes(
            InitialContactId=contact_id or self.contact_id,
            InstanceId=self.instance_id,
            Attributes=formatted_attributes
        )
            
    def stop_chat_streaming(self, contact_id: str = None, streaming_id: str = None):
        """Stop chat streaming for a given contact"""
        try:
            command = dict(
                InstanceId = self.instance_id,
                ContactId = contact_id or self.contact_id,
                StreamingId = streaming_id or self.streaming_id
            )
            response = self.connect.stop_contact_streaming(**command)
            print(f"Stopping chat streaming for contact {contact_id} with streaming ID {streaming_id}")

        except ClientError as e:
            print("Send Message Error")
            print(e.response["Error"]["Code"])
            return None
