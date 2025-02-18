# Generative AI/ML LATAM Samples

This repo provides Generative AI and AI/ML code samples, blueprints (end-to-end solutions) and proof of concepts oriented to the LATAM market

## Getting started

This repo is organized as follows:

### Blueprints

End-to-end solutions for a specific use case. 
  * They include [CloudFormation](https://aws.amazon.com/cloudformation/) templates to provision the solution to your account. 
  * They may include a demo UI.

Here is a list of available blueprints:

| Use Case                                                                                                                                           | Industry                                | Description                    | Type        | Languages                                      |
|----------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------|--------------------------------|-------------|------------------------------------------------|
| [Multipage Document Analysis](./blueprints/multipage-document-analysis/README.md)                                                                  | Financial Services/Legal/Cross-industry | Use this blueprint to extract key information from lengthy documents in highly regulated industries leveraging Amazon Bedrock's wide array of LLMs. | Backend (Pyhton) + UI (React) | Spanish, English                               |
| [Contract Compliance Analysis](https://github.com/aws-samples/generative-ai-cdk-constructs-samples/tree/main/samples/contract-compliance-analysis) | Legal / Cross-industry                  | This project automates the analysis of contracts by splitting them into clauses, determining clause types, evaluating compliance against a customer's legal guidelines, and assessing overall contract risk based on the number of compliant clauses. This is achieved through a workflow that leverages Large Language Models via Amazon Bedrock. | Python for Backend, TypeScript (React) for Frontend | English (can be customized to other languages) |


### Samples
Code samples/notebooks that demonstrate a specific AI/ML functionality in AWS.

Here is a list of available samples:

| Use Case                                                                                | Industry                                | Description                    | Type        | Languages        |
|-----------------------------------------------------------------------------------------|-----------------------------------------|--------------------------------|-------------|------------------|
| [Multi-Agent Collaboration System](samples/multi-agent-collaboration/README.md)                    | Cross Industry | Multi-agent customer support system with escalation capability using AWS CDK and Amazon Bedrock | CDK Python        | Multilanguage |
| [SQL Agent with Amazon Bedrock](samples/sql-bedrock-agent/README.md)                    | Cross Industry, Business Insights |Build and deploy a SQL Agent that lets users query databases using natural language instead of writing SQL code. The implementation combines enterprise features from Amazon Bedrock with LangChain's specialized SQL tools. | CDK Python| Multilanguage |
| [Whatsapp with Agents for Amazon Bedrock](samples/end-user-messaging-bedrock/README.md) | Cross Industry, Customer Experience | Implement a WhatsApp communication channel using AWS End User Messaging for social integration. Integrate your business logic with Amazon Bedrock Agents for AI-powered interactions. | CDK Python| Multilanguage |
| [WhatsApp Integration with Amazon Connect (with voice notes)](samples/whatsapp-eum-connect-chat/README.md) | Cross Industry, Customer Experience | AWS-powered WhatsApp integration with Amazon Connect enabling seamless customer service chat with voice note transcription capabilities. | CDK Python        | Multilanguage |
| [Amazon Connect Custom Bot with Bedrock Agent and Human Escalation](samples/connect-custom-bot/README.md) | Cross Industry, Customer Experience | A custom solution that integrates Amazon Connect with Bedrock AI agents, enabling advanced chatbot interactions and intelligent escalation to human agents, optimizing customer service through sophisticated conversation flows or multi-agent reasoning. | CDK Python        | Multilanguage |
| [Amazon Nova Samples](./samples/amazon-nova-samples/README.md)                          | Cross Industry, Customer Experience | [Amazon Nova](https://aws.amazon.com/ai/generative-ai/nova) family of models samples that cover various use cases (text generation, document processing, content generation, agentic workflows, etc).                                                                    | Jupyter Notebooks | Multilanguage |

### Proof of concepts:
  * Code samples/notebooks that aim to prove a concept in Generative AI or AIML.
  * Research paper techniques implementations
  * Novel tecniques implementations
  * May include Cloudformation / CDK

## Contributing

Please refer to the [CONTRIBUTING](CONTRIBUTING.md) document for further details on contributing to this repository. 
