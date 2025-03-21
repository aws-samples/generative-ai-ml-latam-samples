import boto3
import os


class OrderService:
    def __init__(self) -> None:
        TABLE_NAME = os.environ["ORDER_TABLE_NAME"]
        self.table = boto3.resource("dynamodb").Table(TABLE_NAME)

    def get_order(self, order_number, rut):
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
