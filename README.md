# Generative AI/ML LATAM Samples

This repo provides Generative AI and AI/ML code samples, blueprints (end-to-end solutions) and proof of concepts oriented to the LATAM market

## Getting started

This repo is organized as follows:

### Blueprints

End-to-end solutions for a specific use case. 
  * They include [CloudFormation](https://aws.amazon.com/cloudformation/) templates to provision the solution to your account. 
  * They may include a demo UI.

Here is a list of available blueprints:

| Use Case                                                                                                                                           | Industry                                | Description                                                                                                                                                                                                                                                                                                                                        | Type                                                                                             | Languages                                       |
|----------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|-------------------------------------------------|
| [Multipage Document Analysis](./blueprints/multipage-document-analysis/README.md)                                                                  | Financial Services/Legal/Cross-industry | Use this blueprint to extract key information from lengthy documents in highly regulated industries leveraging Amazon Bedrock's wide array of LLMs.                                                                                                                                                                                                | Backend (Python) + UI (React)                                                                    | Spanish, English                                |
| [Contract Compliance Analysis](https://github.com/aws-samples/generative-ai-cdk-constructs-samples/tree/main/samples/contract-compliance-analysis) | Legal / Cross-industry                  | This project automates the analysis of contracts by splitting them into clauses, determining clause types, evaluating compliance against a customer's legal guidelines, and assessing overall contract risk based on the number of compliant clauses. This is achieved through a workflow that leverages Large Language Models via Amazon Bedrock. | Python for Backend, TypeScript (React) for Frontend                                              |  English (can be customized to other languages) |
| [Smart Product Onboarding](https://github.com/aws-samples/aws-smart-product-onboarding)                                                            | Retail CPG                              | Reimagine the seller product onboarding experience with generative AI to create product titles and descriptions, categorize, and extract attributes.                                                                                                                                                                                               | Backend (Python) + UI (React)  | All languages supported by Amazon Nova and Anthropic Claude models |
| [RFP Answers With Generative AI](https://github.com/aws-samples/generative-ai-cdk-constructs-samples/tree/main/samples/rfp-answer-generation)      | Cross-industry                          | Leverage existing company documents to automate responses to a Request for Proposal (RFP) document.                                                                                                                                                                                                                                                  | Backend (Python) + UI (React)  | English (can be customized to other languages) |
| [Next generation marketing campaigns with Amazon Nova ](./blueprints/genai-marketing-campaigns/README.md)                                          | Retail CPG/Cross-industry/Marketing              | Quickly iterate over ideas for visuals for marketing campaigns and accelerate the creation of visual assets for any marketing campaign with the Amazon Nova family of models.                                                                                                                                                                      | Backend (Pyhton) + UI (React) | English (can be customized to other languages) |
| [Smart Prescription Reader](https://github.com/aws-samples/sample-smart-prescription-reader)                                                       | Healthcare                             | Transform prescription images into structured medical data using AI-powered extraction and validation. | Python for Backend, TypeScript (React) for Frontend | English (can be customized to other languages) |


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
| [WardrobeGenAI Demo](./samples/wardrobe-genai-demo/README.md) | Retail, Customer Experience | AI-powered fashion recommendation system using AWS Bedrock and Anthropic Claude for personalized style suggestions. Features real-time image analysis and interactive shopping experience. | React + Node.js | TypeScript |
|[Claude 3.7 thinking in multimodal](./samples/multimodal-claude-thinking/README.md)| Cross Industry | This project demonstrates Claude 3.7's real-time reasoning processes with text, images, and documents using AWS Bedrock converse API. The repository includes three Jupyter notebooks and a custom interface for observing how the AI model approaches different tasks. | Python| Multilanguage |
|[Amazon Nova Sonic Conversation](./samples/nova-sonic-sample/README.md)|  | A demonstration project showcasing Amazon Bedrock's Nova Sonic model for real-time speech processing and natural voice interactions using bidirectional streaming capabilities. | Python| English |




### Proof of concepts:
  * Code samples/notebooks that aim to prove a concept in Generative AI or AIML.
  * Research paper techniques implementations
  * Novel tecniques implementations
  * May include Cloudformation / CDK

## Contributing

Please refer to the [CONTRIBUTING](CONTRIBUTING.md) document for further details on contributing to this repository. 
