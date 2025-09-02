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


# kb_retrieval.py

import boto3
import os
import json

from aws_lambda_powertools import Logger

from langchain_aws import ChatBedrockConverse
from langchain_aws.embeddings import BedrockEmbeddings
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

from kb_answer_tool.kb_config import KnowledgeBaseConfigSingleton

from kb_answer_tool.prompts.generate_qa_kb_prompts import get_kb_qa_prompt_selector
from kb_answer_tool.prompts.generate_query_augmentation_prompts import get_query_augmentation_prompt_selector

from kb_answer_tool.structured_output.questions import Questions

from botocore.exceptions import ClientError
from botocore.config import Config

AWS_REGION = os.environ.get("AWS_REGION")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION")
MODEL_ID = os.environ.get("KNOWLEDGE_BASE_BEDROCK_MODEL_ID")
EMBEDDINGS_MODEL_ID = os.environ.get("EMBEDDINGS_MODEL_ID")

logger = Logger(service="lawyer_agent", level="DEBUG")

kb_config = KnowledgeBaseConfigSingleton()

logger.debug("Env variables")
logger.debug("AWS_REGION")
logger.debug(AWS_REGION)
logger.debug("BEDROCK_REGION")
logger.debug(BEDROCK_REGION)
logger.debug("MODEL_ID")
logger.debug(MODEL_ID)
logger.debug("EMBEDDINGS_MODEL_ID")
logger.debug(EMBEDDINGS_MODEL_ID)

logger.debug("Knowledge base config")
logger.debug(kb_config.get_dynamodb_summaries_table_name())
logger.debug(kb_config.get_opensearch_host())
logger.debug(kb_config.get_opensearch_port())
logger.debug(kb_config.get_opensearch_index_name())

summaries_table = boto3.resource("dynamodb").Table(kb_config.get_dynamodb_summaries_table_name())
bedrock_runtime = boto3.client('bedrock-runtime')

bedrock_embeddings = BedrockEmbeddings(
    client=bedrock_runtime,
    region_name=BEDROCK_REGION,
    model_id=EMBEDDINGS_MODEL_ID,
    normalize=True,
    model_kwargs={
        "dimensions": 512,
    }
)

rag_llm = ChatBedrockConverse(
    model=MODEL_ID,
    temperature=0.3,
    max_tokens=1000,
    # other params...
)


def retrieve_from_kb(
        oss_client: OpenSearch,
        index_name: str,
        persona: str,
        perspective: str,
        embedding: list[float],
        k: int=3
):
    """
    Given an embedding and some metadata (persona and perspective) retrieve information within the KB to answer the query.

    Args:
        oss_client (str): The client url of the amazon open search serverless collection
        index_name (str): The name of amazon open search serverless index being used for the search
        persona (str): The persona/rol asking the query
        perspective (str): The perspective from which I'm trying to answer the information
        embedding List[float]: The query encoded as an embedding
        k (int): How many similar documents should be returned upon retrieval

    Returns:
        List[str]: A list of documents related to the user's query
    """

    print(f"Looking for data for {persona} and {perspective}")

    matched_qa_pairs = []

    body = {
        "size": k,
        "_source": {
            "exclude": ["embedding"],
        },
        "query":
            {
                "knn":
                    {
                        "embedding": {
                            "vector": embedding,
                            "k": k,
                        }
                    }
            },
        "post_filter": {
            "bool": {
                "filter": [
                    {"term": {"persona": persona}},
                    {"term": {"perspective": perspective}}
                ]
            }
        }
    }

    res = oss_client.search(index=index_name, body=body)

    print("The results")
    print(res)

    for hit in res["hits"]["hits"]:
        matched_qa_pairs.append((hit["_source"]["question"], hit["_source"]["answer"]))

    return matched_qa_pairs


def encode_text(
        text: str,
        dimension: int = 1024,
):
    """
    Get an embedding from a text query using LLMs.

    Args:
        text (str): The text to encode as embedding
        dimension (int): The size of the embedding. 1,024 (default), 384, 256


    Returns:
        List[float]: An embedding of size dimension.
    """

    payload_body = {
        "inputText": text,
        "dimensions": dimension,
        "normalize": True
    }

    logger.debug("embedding text")
    logger.debug(payload_body)

    response = bedrock_runtime.invoke_model(
        body=json.dumps(payload_body),
        modelId=EMBEDDINGS_MODEL_ID,
        accept="application/json",
        contentType="application/json"
    )

    feature_vector = json.loads(response.get("body").read())["embedding"]

    logger.debug("text embedding")
    logger.debug(feature_vector)

    return feature_vector


def get_opensearch_connection(
        host: str,
        port: int,
) -> OpenSearch:
    """
    Establishes a connection to an OpenSearch cluster using AWSV4SignerAuth for authentication.

    Args:
        host (str): The host address of the OpenSearch cluster.
        port (int): The port number on which the OpenSearch cluster is running.

    Returns:
        OpenSearch: A connection object to the OpenSearch cluster.
    """

    # Create an AWSV4SignerAuth instance for authentication
    auth = AWSV4SignerAuth(
        boto3.Session(
            region_name=AWS_REGION
        ).get_credentials(),
        AWS_REGION,
        "aoss"
    )

    # Create an OpenSearch client instance
    client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30,
    )

    # Return the OpenSearch client instance
    return client


def get_meta_kb_summary(
        user: str,
        perspective: str
) -> str:
    """
    Get an existing summary, if exists, for a combination of user and perspective.

    Args:
        persona (str): The persona making a query
        perspective (int): The perspective from which the query is to be answered

    Returns:
        summary: A summary from the meta-knowledge base
    """

    print("Trying to get summary")
    print(f"summary key: {user}-{perspective}")

    try:
        response = summaries_table.get_item(
            Key={
                "summary_key": f"{user}-{perspective}",
            }
        )
        if "Item" in response:
            item = response["Item"]
            return item["summary"]
        else:
            return ""
    except ClientError as ex:
        logger.error(f"Summary for {user}-{perspective} does not exist")
        raise ex


def augment_user_query(
        query: str,
        persona: str,
        mk_summary: str,
) -> list[str]:
    """
    Given a user (assuming a persona/role) query and a summary of a knowledge base. Augment the original query by generating N related queries.

    Args:
        query (str): The query being processed
        persona (str): The persona making a query
        mk_summary (str): The summary from the meta-knowledge base used to answer the query

    Returns:
        summary: A list of N related queries
    """

    query_augmentation_llm = ChatBedrockConverse(
        model=MODEL_ID,
        temperature=0.7,
        max_tokens=500,
        # other params...
    )

    LLM_AUGMENT_QUERY_PROMPT_SELECTOR = get_query_augmentation_prompt_selector(lang="en")
    gen_queries_prompt = LLM_AUGMENT_QUERY_PROMPT_SELECTOR.get_prompt(MODEL_ID)
    structured_queries_generate = gen_queries_prompt | query_augmentation_llm.with_structured_output(Questions)

    augmented_queries = structured_queries_generate.invoke(
        {
            "role": persona,
            "mk_summary": mk_summary,
            "user_query": query
        }
    )

    print("The augmented queries")
    print(augmented_queries)

    return augmented_queries.questions


def qa_chatbot_answer(
        query: str,
        context: str
):
    """
    Given a query, and some context, use an LLM to answer the query according to the context.

    Args:
        query (str): A query made by the user
        context (int): The context in which the query is being asked

    Returns:
        summary: An asnwer to the user's query
    """

    LLM_KB_QA_PROMPT_SELECTOR = get_kb_qa_prompt_selector(lang="en")
    gen_kb_qa_prompt = LLM_KB_QA_PROMPT_SELECTOR.get_prompt(MODEL_ID)
    kb_qa_generate = gen_kb_qa_prompt | rag_llm

    rag_qa = kb_qa_generate.invoke(
        {
            "question": query,
            "context": context
        }
    )

    return rag_qa.content


# 1. Tool Specification
TOOL_SPEC = {
    "name": "kb_answer",
    "description": "Answer a user (assuming a rol/persona) query from a specific perspective.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "user_role": {
                    "type": "string",
                    "description": "The role assumed by the user when asking this query"
                },
                "perspective": {
                    "type": "string",
                    "description": "The perspective from which the user is trying to answer the query",
                },
                "query": {
                    "type": "string",
                    "description": "A query made by the user",
                },
            },
            "required": ["query", "perspective", "user_role"]
        }
    }
}

# 2. Tool Function
def kb_answer(
        tool,
        **kwargs: any
) -> dict:

    """
    Answer a user (assuming a rol/persona) query from a specific perspective.

    Args:

    Returns:
        answer: A comprehensive answer to the query
    """

    qa_str = ""
    qa_pairs = []

    # Extract tool parameters
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]

    # Get parameter values
    role = tool_input.get("user_role")
    perspective = tool_input.get("perspective")
    query = tool_input.get("query")

    #Get Amazon OpenSearch Serverless client
    oss_client = get_opensearch_connection(
        host=kb_config.get_opensearch_host().replace("https://", ""),
        port=kb_config.get_opensearch_port(),
    )

    # Retrieve Meta-Knowledge Base summary
    mkb_summary = get_meta_kb_summary(
        user=role,
        perspective=perspective
    )

    print("The MKB summary")
    print(mkb_summary)

    # Augment user query
    augmented_queries = augment_user_query(
        persona=role,
        query=query,
        mk_summary=mkb_summary
    )
    print("Augment user queries")
    print(augmented_queries)

    # Retrieve QA pairs from KB
    for query in augmented_queries:
        embedding = encode_text(text=query)
        qa_pairs = retrieve_from_kb(
            oss_client=oss_client,
            index_name=kb_config.get_opensearch_index_name(),
            embedding=embedding,
            persona=role,
            perspective=perspective,
            k=3
        )

        qa_str = qa_str.join(f"{qa[0]}: {qa[1]}" for qa in qa_pairs)

    print("The context")
    print(qa_str)

    # Answer query
    answer = qa_chatbot_answer(
        query=query,
        context=qa_str
    )

    print("The given answer")
    print(answer)

    # Return structured response
    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [
            {"text": answer}
        ]
    }

