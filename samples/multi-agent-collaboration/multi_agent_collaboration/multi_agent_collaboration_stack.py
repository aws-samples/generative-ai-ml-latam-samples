import json
from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam, CfnOutput
    # aws_sqs as sqs,
)
from constructs import Construct


DEFAULT_MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
from bedrock_agent import Agent, ActionGroup, build_agent_collaborator_property
from lambdas import Lambdas
from databases import Tables


"""
Main stack class that sets up the multi-agent collaboration infrastructure.
Handles creation and configuration of AWS resources and agents.
"""
class MultiAgentCollaborationStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """
        Initialize the multi-agent collaboration stack.
        
        Args:
            scope: The scope in which to create this stack
            construct_id: The ID of this stack
            kwargs: Additional keyword arguments
        """
        super().__init__(scope, construct_id, **kwargs)

        # Create Tables and Lambda functions,  set up permissions and environment variables
        self._create_and_configure_resources()

        # Create support agent
        self.support_agent = Agent(
            self,
            "SupportAgent",
            action_groups=ActionGroup().from_file(
                "agent_action_group_support_data.json", self.functions.tickets
            ),
            agent_name="collab-tickets",
            agent_description="Ticket Support",
            agent_instruction=(
                "Usted es un amable agente de soporte a cliente que ayuda creando tickets y entregando informacion de tickets de atencion de postventa."
            ),
            foundation_model=DEFAULT_MODEL_ID,
        )
        self.support_agent.create_alias("ticket-alias")

        # Create orders agent
        self.orders_agent = Agent(
            self,
            "OrdersAgent",
            action_groups=ActionGroup().from_file(
                "agent_action_group_order_data.json", self.functions.orders
            ),
            agent_name="collab-orders",
            agent_description="Order Information",
            agent_instruction=(
                "Usted es un amable agente que maneja los pedidos de los clientes y entrega informacion sobre los pedidos."
            ),
            foundation_model=DEFAULT_MODEL_ID,
        )
        self.orders_agent.create_alias("orders-alias")

        # Create escalating agent
        self.escalation_agent = Agent(
            self,
            "Escalating",
            action_groups=ActionGroup().from_file(
                "agent_action_group_escalation_data.json"
            ),
            agent_name="mac-escalation",
            agent_description="Escalation",
            agent_instruction=(
                "Usted es un amable agente que es capaz de escalar casos de cliente a las áreas especialistas"
            ),
            foundation_model=DEFAULT_MODEL_ID,
        )
        self.escalation_agent.create_alias("escalation-alias")


        agent_collaborators = [
            build_agent_collaborator_property(
                self.escalation_agent,
                instruction= "Escalates to human, for issues no being solved with a ticket or customer explicit request", name="escalation"
            ),
            build_agent_collaborator_property(
                self.orders_agent,
                instruction="Use this agent when you need to get the customer's order information",
                name ="orders",
            ),
            build_agent_collaborator_property(
                self.support_agent,
                instruction= "Use this agent when you need to create a customer support ticket or get ticket status, use this before escalation. You can only create tickets and inform status.",
                name="tickets",
            ),
        ]

        self.supervisor_agent = Agent(
            self,
            "SupervisorAgent",
            action_groups=ActionGroup().from_file(
                "agent_action_group_supervisor_data.json"
            ),
            agent_name="supervisor",
            agent_description="Agente de primera linea puede manejar tickets, estado de pedidos y escalamientos",
            agent_instruction=(
                "Usted es un amable Agente de primera linea que puede manejar tickets de soporte, estado de pedidos y escalamientos a personas especialistas. \
                1) si el cliente necesita conocer el estado del pedido puede buscar y entregar esa informacion.\
                2) si el cliente tiene un problema con su pedido primero crea un ticket. \
                3) si ya ha creado un ticket puede entregar el estado del ticket.\
                4) si el ticket no es suficiente, puede escalar a un agente humano para que vea el caso."
            ),
            foundation_model=DEFAULT_MODEL_ID,
            agent_collaboration="SUPERVISOR_ROUTER",
            collaborators=agent_collaborators,
        )

        CfnOutput(self, "SupervisorAgentId", value=self.supervisor_agent.cfn_agent.attr_agent_id)

    def _create_and_configure_resources(self) -> None:
        """
        Create and configure all required AWS resources for the stack.
        This includes databases, lambda functions, and other infrastructure components.
        """

        # Create resources
        self.tables = Tables(self, "Tb")
        self.functions = Lambdas(self, "Fn")

        # Grant permissions
        self.tables.orders.grant_read_data(self.functions.orders)
        self.tables.tickets.grant_read_write_data(self.functions.tickets)

        # Set environment variables
        self.functions.orders.add_environment(
            "ORDER_TABLE_NAME", self.tables.orders.table_name
        )
        self.functions.tickets.add_environment(
            "TICKET_TABLE_NAME", self.tables.tickets.table_name
        )

        # Grant Bedrock permissions
        bedrock_principal = iam.ServicePrincipal("bedrock.amazonaws.com")
        self.functions.orders.grant_invoke(bedrock_principal)
        self.functions.tickets.grant_invoke(bedrock_principal)
