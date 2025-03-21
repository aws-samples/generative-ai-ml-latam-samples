import boto3
import os

from datetime import datetime

"""
Service class for managing support ticket operations.
"""
class TicketService:
    def __init__(self, order_number = "1234567890") -> None:
        """
        Initialize the ticket service.
        
        Args:
            order_number: Default order number to associate with tickets
        """
        TABLE_NAME          = os.environ['TICKET_TABLE_NAME']
        self.table = boto3.resource('dynamodb').Table(TABLE_NAME)
        self.order_number = order_number 

    def get_current_time(self):
        """
        Get the current timestamp in ISO format.
        
        Returns:
            str: Current timestamp in ISO format
        """
        return datetime.now().strftime('%Y%m%d%H%M')

    def cut_ticket(self, session_id, rut, description):
        """
        Create a new support ticket.
        
        Args:
            session_id: The session ID for the ticket
            rut: The RUT (Chilean tax ID) of the customer
            description: Description of the ticket issue
            
        Returns:
            Dict containing the created ticket details
        """

        ticket_number = self.get_current_time()

        item = { 
            "issue_number": ticket_number,
            "contact_id": session_id,
            "order_number": self.order_number,
            "identity_document_number": rut,
            "issue_details": description,
            "status": "open"
        }

        response  = self.table.put_item(Item=item, ReturnValues= "ALL_OLD")
        if response.get("ResponseMetadata").get("HTTPStatusCode") == 200:
            return f"Ticket {ticket_number} created" 
        
        return "Unable to create a ticket please try again later"
    
    def get_ticket(self, ticket_number):
        """
        Retrieve a ticket by its number.
        
        Args:
            ticket_number: The unique ticket number to retrieve
            
        Returns:
            Dict containing ticket details if found
        """
        response = self.table.get_item(Key={"issue_number": ticket_number})
        return response.get("Item")

