import json
from typing import Dict, Any, List
from aws_cdk.aws_lambda import  Function
from bedrock_agent import create_ag_property


class ActionGroup:
    """
    A class to represent an Action Group with its associated data and lambda function.
    """
    def __init__(self):
        """
        Initialize an ActionGroup with its data and optional lambda function.
        
        Args:
            action_group_data: Dictionary containing the action group configuration
            lambda_function: Optional callable to be associated with this action group
        """
        
    def from_object(self, action_group_data: Dict[str, Any]=None, lambda_function: Function = None):
        """
        Initialize an ActionGroup with its data and optional lambda function.
        
        Args:
            action_group_data: Dictionary containing the action group configuration
            lambda_function: Optional callable to be associated with this action group
        """

        action_group_data = self.attach_lambda(action_group_data, lambda_function)
        return create_ag_property(action_group_data)
        

    def from_file(self, file_path: str, lambda_function: Function = None) -> List['ActionGroup']:
        """
        Create ActionGroup instances from a JSON file.
        
        Args:
            file_path: Path to the JSON file containing action group definitions
            lambda_map: Optional dictionary mapping lambda names to their function implementations
            
        Returns:
            List of ActionGroup instances
        """
        
        with open(file_path, 'r') as f:
            action_group_data = json.load(f)
        
        if lambda_function:
            action_group_data = self.attach_lambda(action_group_data, lambda_function)
            
        return create_ag_property(action_group_data)

    def attach_lambda(self, action_groups,  lambda_function: Function):
        """
        Attach a lambda function to this action group.

        Args:
            lambda_function: The lambda function to be associated with this action group
        """
        modified_action_groups = []
        for ag in action_groups:
            ag["lambda_"] = lambda_function.function_arn
            modified_action_groups.append(ag)
        return modified_action_groups
    
