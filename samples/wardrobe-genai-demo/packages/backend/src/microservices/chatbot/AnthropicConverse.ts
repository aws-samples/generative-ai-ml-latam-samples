
  import Anthropic from '@anthropic-ai/sdk';
  import dotenv from 'dotenv';

  dotenv.config();
  export class AntrhopicConvers   {
    private anthropicClient;
    // private params: Anthropic.MessageCreateParams;
    constructor() {
      this.anthropicClient = new Anthropic({
        apiKey: process.env.ANTHROPIC_API_KEY, // defaults to process.env["ANTHROPIC_API_KEY"]
      });

    }
  
 
    public async sendContent(
      content: any,
    ) {

      try {
        const response = await this.anthropicClient.messages.create({
          model: "claude-3-5-sonnet-20241022",
          max_tokens: 1024,
          messages: content
        });
        return response
      } catch (error) {
        console.log("error", error);
      } 
    }
  }