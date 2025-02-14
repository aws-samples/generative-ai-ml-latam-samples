import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

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

    def insert_contact( self, customerId, channel, contactId, participantToken, connectionToken, name, systemNumber):
        try:
            to_update = { "customerId": customerId, "participantToken": participantToken,
                         "connectionToken": connectionToken, "name": name, "channel": channel, "systemNumber": systemNumber
                         }
            attr_names, attr_values, update_expression = build_update_expression( to_update )

            table_update = self.table.update_item(
                Key={"contactId": contactId},
                UpdateExpression=update_expression, ExpressionAttributeNames=attr_names, ExpressionAttributeValues=attr_values, ReturnValues="ALL_NEW")

        except Exception as e:
            print(e)
        else:
            return table_update
        
    def update_contact( self, customerId, channel, contactId, participantToken, connectionToken, name, systemNumber):
        try:
            to_update = { "customerId": customerId, "participantToken": participantToken,
                         "connectionToken": connectionToken, "name": name, "channel": channel, "systemNumber": systemNumber
                         }
            attr_names, attr_values, update_expression = build_update_expression( to_update )

            table_update = self.table.update_item(
                Key={"contactId": contactId},
                UpdateExpression=update_expression, ExpressionAttributeNames=attr_names, ExpressionAttributeValues=attr_values, ReturnValues="UPDATED_NEW")

        except Exception as e:
            print(e)
        else:
            return table_update



    def get_contact(self, customerId, index_name = "customerId-index"):
        contactId = None
        response = self.table.query(IndexName=index_name, KeyConditionExpression=Key("customerId").eq(customerId))

        if response["Items"]: contactId = response["Items"][0]

        return contactId


    def remove_contactId(self, contactId):

        try:
            self.table.delete_item(Key={"contactId": contactId})
        except Exception as e:
            print(e)
        else:
            return


    def get_connectionToken(self, contactId):
        connectionToken = None
        response = self.table.query(KeyConditionExpression=Key("contactId").eq(contactId))
        if response["Items"]: connectionToken = response["Items"][0]["connectionToken"]
        return connectionToken


    def get_customer(self, contactId):
        customer = None
        response = self.table.query(KeyConditionExpression=Key("contactId").eq(contactId))
        if response["Items"]: customer = response["Items"][0]
        return customer
