from aws_cdk import (Stack, aws_iam as iam)

DEFAULT_MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
from bedrock_agent import Agent, ActionGroup
from lambdas import Lambdas
from databases import Tables

from constructs import Construct

class MultiUserMemorySessionStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Tables and Lambda functions,  set up permissions and environment variables
        self._create_and_configure_resources()

        # Create orders agent
        order_action_groups = ActionGroup().from_file(
            "agent_action_group_order_data.json", self.functions.orders
        )
        self.orders_agent = Agent(
            self,
            "OrdersAgent",
            action_groups=order_action_groups,
            agent_name="mac-orders",
            agent_description="Order Information",
            agent_instruction=(
                "Usted es un amable agente que maneja los pedidos de los clientes y entrega informacion sobre los pedidos."
            ),
            foundation_model=DEFAULT_MODEL_ID,
        )

        



    def _create_and_configure_resources(self) -> None:

        # Create resources
        self.tables = Tables(self, "Tb")
        self.functions = Lambdas(self, "Fn")

        # Grant permissions
        self.tables.orders.grant_read_data(self.functions.orders)

        # Set environment variables
        self.functions.orders.add_environment(
            "ORDER_TABLE_NAME", self.tables.orders.table_name
        )

        # Grant Bedrock permissions
        bedrock_principal = iam.ServicePrincipal("bedrock.amazonaws.com")
        self.functions.orders.grant_invoke(bedrock_principal)
