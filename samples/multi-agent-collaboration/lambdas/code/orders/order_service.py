import boto3
import os


"""
Service class for managing order-related operations.
"""
class OrderService:
    def __init__(self) -> None:
        """Initialize the order service with DynamoDB client."""
        TABLE_NAME = os.environ["ORDER_TABLE_NAME"]
        self.table = boto3.resource("dynamodb").Table(TABLE_NAME)

    def get_order(self, order_number, rut):
        """
        Retrieve an order by its number and RUT.
        
        Args:
            order_number: The unique order number
            rut: The RUT (Chilean tax ID) associated with the order
            
        Returns:
            Dict containing order details if found
        """
        response = self.table.get_item(Key={"order_number": order_number})
        item = response.get("Item")
        if item:
            print("Item:", response.get("Item"))
            if item.get("identity_document_number") == rut:
                data = dict(
                    status=item.get("status"),
                    delivery_date=item.get("delivery_date"),
                    shipping_address=item.get("shipping_address"),
                )
                return data
            else:
                return dict(status="RUT no encontrado")
        else:
            return dict(status="Pedido no encontrado")
