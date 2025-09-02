# MIT No Attribution
#
# Copyright 2025 Amazon Web Services
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import boto3

from aws_lambda_powertools import Logger

from kb_answer_tool.kb_config import KnowledgeBaseConfigSingleton

logger = Logger(service="lawyer_agent", level="DEBUG")

ssm_client = boto3.client('ssm')


def get_ssm_parameters():
    """Retrieve SSM Parameter Store values for knowledge base configuration"""
    
    parameter_names = [
        '/dataIngestionBackend/knowledge_base/dynamodb-metakb-summary-table-name',
        '/dataIngestionBackend/knowledge_base/opensearch-serverless-host',
        '/dataIngestionBackend/knowledge_base/opensearch-serverless-index',
        '/dataIngestionBackend/knowledge_base/opensearch-serverless-port'
    ]
    
    try:
        response = ssm_client.get_parameters(
            Names=parameter_names,
            WithDecryption=True
        )
        
        parameters = {}
        for param in response['Parameters']:
            param_name = param['Name'].split('/')[-1]  # Get the last part of the parameter name
            parameters[param_name] = param['Value']
        
        # Check if all required parameters were retrieved
        missing_params = []
        for name in parameter_names:
            param_key = name.split('/')[-1]
            if param_key not in parameters:
                missing_params.append(name)
        
        if missing_params:
            logger.error(f"Missing SSM parameters: {missing_params}")
            raise Exception(f"Failed to retrieve SSM parameters: {missing_params}")
        
        return parameters
        
    except Exception as e:
        logger.error(f"Error retrieving SSM parameters: {str(e)}")
        raise Exception(f"Failed to retrieve SSM parameters: {str(e)}")


def initialize_kb_config():
    """Initialize the knowledge base configuration with SSM parameters"""
    try:
        ssm_params = get_ssm_parameters()
        
        kb_config = KnowledgeBaseConfigSingleton(
            opensearch_host=ssm_params['opensearch-serverless-host'],
            opensearch_port=int(ssm_params['opensearch-serverless-port']),
            opensearch_index=ssm_params['opensearch-serverless-index'],
            summaries_dynamodb_table=ssm_params['dynamodb-metakb-summary-table-name']
        )
        
        logger.info("Knowledge base configuration initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize knowledge base configuration: {str(e)}")
        raise


# Initialize knowledge base configuration with SSM parameters
initialize_kb_config()