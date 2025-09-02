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


# query_categorization.py

from langchain_aws import ChatBedrockConverse

from query_categorization_tool.user_analysis_mapping import (AnalysisPerspectives, AnalysisPersonas)

from query_categorization_tool.prompts.generate_query_augmentation_prompts import get_query_categorization_prompt_selector

from query_categorization_tool.structured_output.questions import QuestionCategorization

AWS_REGION = 'us-east-1'
BEDROCK_REGION = 'us-east-1'
#MODEL_ID = 'us.amazon.nova-lite-v1:0'
MODEL_ID = 'us.anthropic.claude-3-5-haiku-20241022-v1:0'

categorization_llm = ChatBedrockConverse(
    model=MODEL_ID,
    temperature=0.2,
    max_tokens=500,
    # other params...
)

# 1. Tool Specification
TOOL_SPEC = {
    "name": "query_categorization",
    "description": "Categorize a query into which user roles and perspectives are most useful to answer it.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A query made by the user",
                },
            },
            "required": ["query"]
        }
    }
}

# 2. Tool function
def query_categorization(
        tool,
        **kwargs: any
):

    """
    Categorize a query into which user roles and perspectives are most useful to answer it.

    Args:

    Returns:
        query_categorization: A dictionary with the roles and perspectives the query has been categorized
    """

    # Extract tool parameters
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]

    # Get parameter values
    query = tool_input.get("query")

    LLM_QUERY_CATEGORIZATION_PROMPT_SELECTOR = get_query_categorization_prompt_selector(lang="en")
    categorize_query_prompt = LLM_QUERY_CATEGORIZATION_PROMPT_SELECTOR.get_prompt(MODEL_ID)
    categorize_queries_chain = categorize_query_prompt | categorization_llm.with_structured_output(QuestionCategorization)

    query_categorization = categorize_queries_chain.invoke(
        {
            "query": query,
            "roles_categories": AnalysisPersonas,
            "n_categories": 1
        }
    )

    print(query_categorization)

    # Return structured response
    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [
            {"json": query_categorization.model_dump()}
        ]
    }