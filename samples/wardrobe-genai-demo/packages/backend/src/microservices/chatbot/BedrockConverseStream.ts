import {
    BedrockRuntimeClient,
    ConverseStreamCommand,
    Message,
    ConversationRole,
    InferenceConfiguration,
    ContentBlock,
    ConverseStreamCommandInput,
    SystemContentBlock,
    ConverseStreamOutput,
    MessageStartEvent,
    ContentBlockStartEvent,
    ContentBlockDeltaEvent,
    ContentBlockStopEvent,
    MessageStopEvent,
    ConverseStreamMetadataEvent,
  } from "@aws-sdk/client-bedrock-runtime";
  import { EventEmitter } from "stream";
  
  
  export interface BedrockConverseStreamConfig extends InferenceConfiguration {
    modelId: string;
    defaultSystemContent: string;
    region?: string;
  }
  
  export class BedrockConversaError extends Error {
    constructor(message: string) {
      super(message);
    }
  }
  
  export class BedrockConverseStream extends EventEmitter {
    private bedrockClient: BedrockRuntimeClient;
    private messages: Message[] = [];
    private inferenceConfig: InferenceConfiguration = {};
    private modelId: string;
    private systemContentBlocks: Map<string, SystemContentBlock[]> = new Map();
  
    constructor(config: BedrockConverseStreamConfig) {
      super();
      this.bedrockClient = new BedrockRuntimeClient({ region: config.region , });
      this.inferenceConfig = config;
      this.modelId = config.modelId;
      this.systemContentBlocks.set("default", [
        { text: config.defaultSystemContent },
      ]);
    }
  
    private processStreamOutput(
      output: ConverseStreamOutput
    ): string | undefined {
      return ConverseStreamOutput.visit(output, {
        messageStart: (value) => this.handleMessageStart(value),
        contentBlockStart: (value) => this.handleContentBlockStart(value),
        contentBlockDelta: (value) => this.handleContentBlockDelta(value),
        contentBlockStop: (value) => this.handleContentBlockStop(value),
        messageStop: (value) => this.handleMessageStop(value),
        metadata: (value) => this.handleMetadata(value),
        internalServerException: (value) => {
          return this.handleConversationError(
            `Internal Server Error: ${value.message}`
          );
        },
        modelStreamErrorException: (value) => {
          return this.handleConversationError(
            `Model Stream Error: ${value.message}`
          );
        },
        validationException: (value) => {
          return this.handleConversationError(
            `Validation Error: ${value.message}`
          );
        },
        throttlingException: (value) => {
          return this.handleConversationError(
            `Throttling Error: ${value.message}`
          );
        },
        serviceUnavailableException: (value) => {
          return this.handleConversationError(
            `Service Unavailable: ${value.message}`
          );
        },
        _: (name, value) => {
          return this.handleConversationError(`Unknown type: ${name}`);
        },
      });
    }
  
    private handleMessageStart(
      messageStartEvent: MessageStartEvent
    ): string | undefined {
      console.log("messageStart", messageStartEvent);
      this.emit("messageStart", messageStartEvent);
      return undefined;
    }
  
    private handleContentBlockStart(
      contentBlockStartEvent: ContentBlockStartEvent
    ): string | undefined {
      console.log("contentBlockStart", contentBlockStartEvent);
      this.emit("contentBlockStart", contentBlockStartEvent);
      return undefined;
    }
  
    private handleContentBlockDelta(
      contentBlockDeltaEvent: ContentBlockDeltaEvent
    ): string | undefined {
      console.log("contentBlockDelta", contentBlockDeltaEvent);
      this.emit("contentBlockDelta", contentBlockDeltaEvent);
      return contentBlockDeltaEvent.delta?.text;
    }
  
    private handleContentBlockStop(
      contentBlockStopEvent: ContentBlockStopEvent
    ): string | undefined {
      console.log("contentBlockStop", contentBlockStopEvent);
      this.emit("contentBlockStop", contentBlockStopEvent);
      return undefined;
    }
  
    private handleMessageStop(
      messageStopEvent: MessageStopEvent
    ): string | undefined {
      console.log("messageStop", messageStopEvent);
      this.emit("messageStop", messageStopEvent);
      return undefined;
    }
  
    private handleMetadata(
      metadata: ConverseStreamMetadataEvent
    ): string | undefined {
      console.log("metadata", metadata);
      this.emit("metadata", metadata);
      return JSON.stringify(metadata);
    }
  
    private handleConversationError(message: string) {
      const error = new BedrockConversaError(message);
      console.error(error);
      this.emit("error", error);
      return undefined;
    }
  
    public async sendContent(
      content: ContentBlock[],
      role: ConversationRole = ConversationRole.USER,
      systemContentKey: string = "default"
    ) {
      this.messages.push({ role, content });
      const systemContentBlocks =
        this.systemContentBlocks.get(systemContentKey) || [];
      const input: ConverseStreamCommandInput = {
        modelId: this.modelId,
        messages: this.messages,
        system: systemContentBlocks,
        inferenceConfig: this.inferenceConfig,
      };
      const command = new ConverseStreamCommand(input);
      try {
        const response = await this.bedrockClient.send(command);
        const stream = response.stream;
        if (stream) {
          for await (const event of stream) {
            if (event) {
              const result = this.processStreamOutput(event);
              console.log("result", result);
            }
          }
        }
      } catch (error) {
        this.emit("error", error);
      } finally {
        return { messages: this.messages };
      }
    }
  
    public async sendText(
      text: string,
      role: ConversationRole = ConversationRole.USER
    ) {
      return this.sendContent([{ text }], role);
    }
  }