from IPython.display import display, Markdown, clear_output
# for nice outputs in jupyter notebooks

import json
from typing import List, Dict, Union, Optional
from botocore.config import Config
import boto3

DEFAULT_MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"


config = Config(
   retries = {
      'max_attempts': 10,
      'mode': 'adaptive'
   }
)

class ClaudeThink:
    def __init__(
        self,
        model_id: str = DEFAULT_MODEL_ID,
        budget_tokens: int = 2048,
        max_tokens: int = 4096,
    ):
        """Initialize Claude conversation manager.

        Args:
            model_id: The model identifier to use (defaults to Claude v2)
            budget_tokens: Maximum context tokens for input (defaults to 2048)
            max_tokens: Maximum tokens for completion (defaults to 4096)
        """
        self.model_id = model_id
        self.budget_tokens = budget_tokens
        self.max_tokens = max_tokens
        self.thinking_enabled = True if budget_tokens else False
        self.conversation: List[Dict] = []
        self.reasoning_config = {"thinking": {"type": "enabled", "budget_tokens": self.budget_tokens}}


        # Initialize Bedrock client
        self.client = boto3.client(service_name="bedrock-runtime", config=config)

    def converse_stream(self, content) -> str:
        """Get completion from Claude model based on conversation history.

        Returns:
            str: Model completion text
        """
        # Format conversation history for Claude
        messages = [msg for msg in self.conversation]

        # Invoke model
        response = self.client.converse_stream(
            modelId=self.model_id,
            inferenceConfig=dict(maxTokens=self.max_tokens),
            messages=[*messages, {"role": "user", "content": content}],
            additionalModelRequestFields=self.reasoning_config,
        )
        reasoning = []
        final_text = []


        for chunk in response["stream"]:
            if "contentBlockDelta" in chunk:
                delta = chunk.get("contentBlockDelta", {}).get("delta", {})
                if delta.get("reasoningContent", {}).get("text"):
                    text = delta.get("reasoningContent").get("text")
                    reasoning.append(text)
                if delta.get("text"):
                    text = delta.get("text")
                    final_text.append(text)

                reasoning_md = "".join([f"{r}" for r in reasoning])
                final_text_md = "".join([f"{t}" for t in final_text])
                clear_output(wait=True)

            
                cell_output = f"***Thinking...***\n\n <em>{reasoning_md}</em>"
                if len(final_text):
                    cell_output += f"\n\n***Final Answer:***\n\n {final_text_md} "

                display(Markdown(cell_output))



        self.conversation.append({"role": "user", "content": content})

        reasoning_text = "".join(reasoning)   
        final_text_text  = "\n".join(final_text)   

        self.conversation.append(
            {"role": "assistant", "content": [
               # {"reasoningContent": reasoning_text}, # not acceptable
                {"text": final_text_text}]}
        )





        return reasoning_text, final_text_text

    def clear_conversation(self) -> None:
        """Clear the conversation history."""
        self.conversation = []
