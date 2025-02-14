import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
import time
import os


def build_update_expression(to_update):
    attr_names = {}
    attr_values = {}
    update_expression_list = []
    for i, (key, val) in enumerate(to_update.items()):
        attr_names[f"#item{i}"] = key
        attr_values[f":val{i}"] = val

    for par in zip(attr_names.keys(), attr_values.keys()):
        update_expression_list.append(f"{par[0]} = {par[1]}")
    return attr_names, attr_values, f"SET {', '.join(update_expression_list)}"


class ConnectionsService:
    def __init__(self, connections_table_name=os.environ.get("TABLE_NAME")) -> None:
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(connections_table_name)

    def save_chat_contact_details(self, contact_id: str, connection_token: str, streaming_id: str) -> None:
        """Save chat contact details to DynamoDB"""
        ttl = int(time.time()) + (60 * 60)  # 1 hour

        
        item = {
            'contactId': contact_id,
            'connectionToken': connection_token,
            'streamingId': streaming_id,
            'ttl': ttl
        }
        
        try:
            response = self.table.put_item(Item=item)
            print("Save contact details", {"item": item, "response": response})
        except ClientError as e:
            print("Save Contact Error")
            print(e.response["Error"]["Code"])
            return None
