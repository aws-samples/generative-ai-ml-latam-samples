import boto3
import os
import sys
from botocore.exceptions import ClientError

participant_client = boto3.client("connectparticipant")
connect_client = boto3.client("connect")


class ChatService:
    """
    Service class for managing Amazon Connect chat interactions.
    
    This class provides methods to interact with Amazon Connect chat functionality,
    including starting and managing chat sessions, handling participant connections,
    and managing chat configuration.
    """
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

    def send_message(self, message: str, connectionToken: str) -> None:
        response = self.participant.send_message(
            ContentType="text/plain", Content=message, ConnectionToken=connectionToken
        )
        return response

    def start_stream(self, ContactId: str) -> str:
        """
        Initialize a streaming session for a chat contact.
        
        Args:
            ContactId (str): The ID of the contact to start streaming for
            
        Returns:
            str: The streaming session ID if successful
        
        Raises:
            Exception: If the streaming session cannot be started
        """
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


        

    def start_chat_and_stream(self, message: str, phone: str, channel: str, name: str = "unknown", systemNumber: str = "unknown") -> dict:
        """
        Create a chat contact and initialize streaming for it.
        
        This method combines chat creation and streaming setup into a single operation
        to simplify the chat initialization process.
        
        Args:
            message (str): Initial message to send in the chat
            phone (str): Contact phone number
            channel (str): Communication channel identifier
            name (str, optional): Contact display name. Defaults to "unknown"
            systemNumber (str, optional): System identifier. Defaults to "unknown"
            
        Returns:
            dict: Contains contactId, participantToken, and connectionToken for the chat
            
        Raises:
            Exception: If chat creation or streaming setup fails
        """
        start_chat_response         = self.start_chat(message, phone, channel, name, systemNumber)

    
        participantToken             = start_chat_response["ParticipantToken"]
        contactId                   = start_chat_response['ContactId']
        
        start_stream_response       = self.start_stream(contactId)
        create_connection_response  = self.create_connection(participantToken)
        connectionToken             = create_connection_response['ConnectionCredentials']['ConnectionToken']

        return contactId, participantToken, connectionToken

    def create_connection(self, ParticipantToken: str) -> dict:

        create_connection_response = self.participant.create_participant_connection(
            Type=["CONNECTION_CREDENTIALS"],
            ParticipantToken=ParticipantToken,
            ConnectParticipant=True
        )
        return create_connection_response

    def get_signed_url(self, connectionToken: str, attachment: dict) -> str:
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

    def attach_file(self, fileContents: bytes, fileName: str, fileType: str, ConnectionToken: str) -> None:
        # Method to attach a file to the chat
        # Parameters:
        #   fileContents: Contents of the file to attach
        #   fileName: Name of the file
        #   fileType: MIME type of the file
        #   ConnectionToken: Token for the chat connection
        # Returns: None
        # Raises: NotImplementedError
        raise NotImplementedError("File attachment functionality not yet implemented")

    def create_participant(self, contact_id: str) -> dict:
        """
        Create a new participant for a chat session.
        
        This method creates a new participant in the Amazon Connect chat and
        generates the necessary credentials and tokens.
        
        Args:
            contact_id (str): The contact ID to create the participant for
            
        Returns:
            dict: Participant details including ID and credentials
            
        Raises:
            Exception: If participant creation fails
        """
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
        

    def create_participant_connection(self, token: str) -> dict:
        """
        Create a connection for a chat participant.
        
        Args:
            token (str): The participant's authentication token
            
        Returns:
            dict: Connection details including credentials and tokens
            
        Raises:
            Exception: If connection creation fails
        """
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


    def send_message(self, connection_token: str, message: str, content_type: str = "text/plain"):
        """Send a message in the chat"""
        command = dict(
            ContentType = content_type,
            Content = message,
            ConnectionToken = connection_token
        )
        
        try:
            response = self.participant.send_message(**command)
            print("Sending message", {"command": command, "response": response})
            return response.get('Id')
        except ClientError as e:
            print("Send Message Error")
            print(e.response["Error"]["Code"])
            return None
