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


import os
import json
import logging

from prompt_selector.generate_writer_prompt import get_writer_prompt_selector

from strands import Agent, tool
from strands.models import BedrockModel

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

app = BedrockAgentCoreApp()
logger = logging.getLogger(__name__)

BEDROCK_MODEL_ID = os.environ["AGENT_BEDROCK_MODEL_ID"]

class InvocationRequest(BaseModel):
    input: Dict[str, Any]

class InvocationResponse(BaseModel):
    output: Dict[str, Any]

app = FastAPI(title="Writer Agent Server", version="1.0.0")

@app.post("/invocations", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    """Given a set of QA and an objective, write a section of a compliance report"""

    payload = request.input
    logger.debug(f"Received payload: {payload}")

    industry = payload["industry"]
    country = payload["country"]
    workload = payload["workload"]
    qa_set = payload["questions"]
    section = payload["section"]
    section_number = payload["section_number"]
    description = payload["description"]

    LLM_WRITE_SECTION_REPORT_PROMPT_SELECTOR = get_writer_prompt_selector(lang="en")
    write_report_prompt = LLM_WRITE_SECTION_REPORT_PROMPT_SELECTOR.get_prompt(BEDROCK_MODEL_ID)

    messages = write_report_prompt.format_messages(
        industry=industry,
        country=country,
        workload=workload,
        section_name=section,
        section_number=section_number,
        section_description=description,
        qa_set=qa_set
    )

    logger.debug("messages")
    logger.debug(messages)

    model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
    )

    writer_agent = Agent(
        model=model,
        system_prompt=messages[0].content
    )

    try:
        writer_agent_completion = writer_agent(messages[1].content)
        markdown_report = writer_agent_completion.message['content'][-1]['text']
        logger.debug("The markdown report")
        logger.debug(markdown_report)

        response = {
            "status": 200,
            "content-type": "text",
            "body": {
                "content": markdown_report
            }
        }

        return InvocationResponse(output=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")


@app.get("/ping")
async def ping():
    return {
    "status": "healthy",
    "time_of_last_update":datetime.now().timestamp()
    }

