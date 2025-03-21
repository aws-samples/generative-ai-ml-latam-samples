from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam,
)
from constructs import Construct


class CreateAgentRole(Construct):

    def __init__(
        self, scope: Construct, construct_id: str, base_name=None, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        stk = Stack.of(self)
        _account = stk.account
        _region = stk.region
        _stack_name = stk.stack_name

        if not (base_name):
            base_name = _stack_name

        self.service_role = iam.Role(
            self,
            "Role",
            role_name=f"AgentsRole_{base_name}",
            assumed_by=iam.ServicePrincipal(
                "bedrock.amazonaws.com",
                conditions={
                    "StringEquals": {"aws:SourceAccount": _account},
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:bedrock:{_region}:{_account}:agent/*"
                    },
                },
            ),
        )
        # Added support for cross-region inference
        self.service_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel*", "bedrock:CreateInferenceProfile"],
                resources=[
                    "arn:aws:bedrock:*::foundation-model/*",
                    "arn:aws:bedrock:*:*:inference-profile/*",
                    "arn:aws:bedrock:*:*:application-inference-profile/*",
                ],
            )
        )

        self.service_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:GetInferenceProfile",
                    "bedrock:ListInferenceProfiles",
                    "bedrock:DeleteInferenceProfile",
                    "bedrock:TagResource",
                    "bedrock:UntagResource",
                    "bedrock:ListTagsForResource",
                ],
                resources=[
                    "arn:aws:bedrock:*:*:inference-profile/*",
                    "arn:aws:bedrock:*:*:application-inference-profile/*",
                ],
            )
        )

        self.service_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:GetAgentAlias",
                    "bedrock:InvokeAgent",
                ],
                resources=[
                    "arn:aws:bedrock:*:*:agent/*",
                    "arn:aws:bedrock:*:*:agent-alias/*",
                ],
            )
        )

        self.knowledge_base_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["bedrock:Retrieve"],
            resources=[f"arn:aws:bedrock:{_region}:{_account}:knowledge-base/*"],
        )

        self.service_role.add_to_policy(self.knowledge_base_policy)
