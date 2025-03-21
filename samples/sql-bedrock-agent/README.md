
# Amazon Bedrock SQL Agent

## Overview
This project shows you how to build and deploy a powerful SQL Agent that lets users query databases using natural language instead of writing SQL code. The implementation combines enterprise features from Amazon Bedrock (security, monitoring, API management) with LangChain's specialized SQL tools.


## What is a SQL Agent?
A SQL Agent is an Generative AI-powered aplication that enables users to interact with databases using natural language. Instead of writing SQL queries directly, users can ask human questions and receive natural respones. For example

| User Question | Agent response |
|-|-|
|Tell me about December sales?| December 2024 has 12.5M in sales|
|What about Dec 2023| December 2023 has 9.763 M |
|Top Purchased products| The most purchased products are: Sneakers with 246K sales, Smartphone with 187K, ...|


Here we implement the main SQL Agent Logic by leveraging [Langchain SQL Agent](https://python.langchain.com/v0.1/docs/use_cases/sql/agents/). This provides useful tools right out of the box:

```python
for t in  agent_executor.tools:
    print (f"{t.name}:")
    print(t.description, end="\n\n")
```
output:
```cmd
sql_db_query:
Input to this tool is a detailed and correct SQL query, output is a result from the database. If the query is not correct, an error message will be returned. If an error is returned, rewrite the query, check the query, and try again. If you encounter an issue with Unknown column 'xxxx' in 'field list', use sql_db_schema to query the correct table fields.

sql_db_schema:
Input to this tool is a comma-separated list of tables, output is the schema and sample rows for those tables. Be sure that the tables actually exist by calling sql_db_list_tables first! Example Input: table1, table2, table3

sql_db_list_tables:
Input is an empty string, output is a comma-separated list of tables in the database.

sql_db_query_checker:
Use this tool to double check if your query is correct before executing it. Always use this tool before executing a query with sql_db_query!
```

That means: 
- This agent can discover the list of tables
- Construct sql statement based on those tables and sample rows
- Check if the generated query is correct and execute it.
- If there is an error it can also iterate by modifying and executing the new version. 

Amazing right?

Let's see how we can implement this in an AWS.


## Architecture

![](./SQL_Agent.jpg)

The architecture here is simple, minimal components involved (Amazon Bedrock and AWS Lambda). The flow when user ask a question is:

1. User ask in natural language something that could be answered with a query (example: "sales by country and product"). This query is sent to Amazon Bedrock Agent using `invoke_agent` method.
2. The Agent in bedrock decides which action group (AG) to use (action groups [define what the agent can do](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-action-create.html)). In this case it goes with SQLAgent AG.
3. Here is where the business logic resides in form of code executed by AWS Lambda functions. This actions can be from [retrieve documents from a knowledge base](https://aws.amazon.com/bedrock/knowledge-bases/) to [invoke external APIs](https://github.com/aws-samples/bedrock-agent-and-telecom-apis). In this case, we use a SQL Lite DB connection just as proof of concept ( [you can easily connect AWS Lambda with Aurora PostgreSQL and MySQL using RDS Data API](https://aws.amazon.com/blogs/database/using-the-data-api-to-interact-with-an-amazon-aurora-serverless-mysql-database/) and also [classic db clients](https://docs.aws.amazon.com/lambda/latest/dg/services-rds.html)). Here we use an LLM in the execution of the Langchain SQL Agent.
4. After retrieving the results, we pass back the response to Amazon Bedrock Agent that handles the user conversation.

## So why using two agents (one from Bedrock and one inside the Lambda)?

[Amazon Bedrock Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html) are managed autonomous agents that orchestrate interactions between foundation models, data sources, and APIs to complete user tasks through natural conversation. They automatically handle prompt engineering, memory, monitoring, and API invocations without requiring infrastructure management. 

In other hand, [LangChain](https://python.langchain.com/docs/introduction/) is a composable framework to build with LLMs. You can leverage LangChain agents within Bedrock's action groups to:
1. Get the best of both worlds, Bedrock's managed infrastructure and LangChain's flexible tooling. Use LangChain's specialized tools and custom agents while maintaining Bedrock's enterprise features.
2. Provide API interface for applications to interact with Amazon Bedrock Agent.
3. You can grow your Bedrock Agent functionality by adding more action groups. For example one AG for Data Wharehouse (structured) while other consulting Knowledge Base (unstructured documents) 

In essence, you could use Bedrock for the main orchestration, infraestructure, security, tracing, monitoring and conversation memory, while implementing specific  actions through LangChain agents when needed.

Let's deploy this agent.

## Prerequisites

### CDK Setup

Note: If you you don't know what CDK is, please [start here](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html) and install cdk and dependencies, configure environment and boostrap your account and region.


### Cross Region Inference

[Cross Region Inference](https://aws.amazon.com/blogs/machine-learning/getting-started-with-cross-region-inference-in-amazon-bedrock/) dynamically routes LLM invocations across multiple regions. In this project, you will be using an [Inferece Profile](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html) which is resource that represent the same model ID in different regions. 

You will find this inference profile ID in [project_lambdas.py](./lambdas/project_lambdas.py)

```python
DEFAULT_MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
# Regions covered
# US East (Virginia) us-east-1,
# US East (Ohio) us-east-2,
# US West (Oregon) us-west-2
```
### Model Access

Here we are using [Anthopic Claude Haiku 3.5](https://aws.amazon.com/about-aws/whats-new/2024/11/anthropics-claude-3-5-haiku-model-amazon-bedrock/) vía Amazon Bedrock API. If you are new to Bedrock, probably you need to [enable model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) for this specific model in all regions covered by the inference profile (at least the region you are deploying this)



## Deployment

This project uses AWS CDK for infrastructure deployment. Follow these steps:

Clone the repo:
```bash
git clone https://github.com/aws-samples/generative-ai-ml-latam-samples
```

Set up environment:
```bash
cd samples/sql-bedrock-agent
python3 -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate.bat
pip install -r requirements.txt
```

Deploy the stack:
```bash
cdk deploy
```

## Langchain SQL Agent 

You will find the SQL Agent implementation in [lambda_function.py](./lambdas/code/sql_agent/lambda_function.py)

```python
from langchain_community.agent_toolkits import create_sql_agent
from langchain_aws import  ChatBedrock
from langchain_community.utilities.sql_database import SQLDatabase

model_id = os.environ.get("MODEL_ID", "us.anthropic.claude-3-5-haiku-20241022-v1:0")

db = SQLDatabase.from_uri("sqlite:///Chinook.db") # same toy database from https://python.langchain.com/v0.1/docs/use_cases/sql/agents/

llm = ChatBedrock(model = model_id,  beta_use_converse_api=True, model_kwargs={"temperature": 0})
agent_executor = create_sql_agent(llm, db=db, verbose=True)
```

And for every user query you invoke this `agent_executor` 

```python
def query_db(consulta):
    response = agent_executor.invoke(consulta)
    return response.get("output")
```

## Testing your agent

To test the SQL Agent:
1. Navigate to the Amazon Bedrock console
2. Find your deployed agent
3. Use the test environment to send natural language queries
4. Verify the responses and SQL query execution

Example queries:
- "que información puedes proveer?"
- "What are the top 5 customers by revenue?"
- "Cuales son los empleados con más ventas?"
- "Los discos más vendidos en Chile" Follow up with "And Argentina?"

Demo

![](test_agent.gif)

## Where to go from here?

If you want to dive deep on Text 2 SQL techniques, you can follow this [excelent workshop](https://github.com/aws-samples/text-to-sql-bedrock-workshop/) about the topic. Which also covers some enterprise cases you may be asking: 
* How to deal with hundred or maybe thousands of tables?
* How to measure accuracy? (Query and Responses)
* How to improve query generation with in-context learning and Fine tuning a model to perform this task
* How to improve security, prevent query injection


Also is recommended to follow [Langchain Approach](https://python.langchain.com/v0.1/docs/use_cases/sql/agents/) for large databases, high cardinality tables and query validation. 

## Security

Finally a word for [Amazon Bedrock Security](https://docs.aws.amazon.com/bedrock/latest/userguide/security.html). Read about it and learn you how to configure Amazon Bedrock to meet your security and compliance objectives


## Cost Considerations

The main cost components for this project are:
  - [Amazon Bedrock](https://aws.amazon.com/bedrock/pricing). Just the input / output tokens for Haiku 3.5 (if your are using the inference profile as-is). There is no additional charges for using Bedrock Agents.
  - [AWS Lambda](https://aws.amazon.com/lambda/pricing/) probably you will fall under [free tier](https://aws.amazon.com/lambda/pricing/) for this demo (1 million free requests per month and 400,000 GB-seconds of compute time per month)

This is a serverless pay-as-you-go architecture (0 cost when no using it)

## Decomission

In order to delete resources, ust `cdk destroy` if using cdk cli. Alternately go to cloudformation console an hit `Delete`

Enjoy!
