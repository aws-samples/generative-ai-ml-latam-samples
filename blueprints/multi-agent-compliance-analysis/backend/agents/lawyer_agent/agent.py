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
import logging
import json
import traceback
import boto3

from strands import Agent, tool
from strands.models import BedrockModel

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from kb_answer_tool import kb_answer
from query_categorization_tool import query_categorization
from prompt_selector.generate_lawyer_prompt import get_lawyer_prompt_selector
from structured_output.LawyerResponse import LawyerResponse

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BEDROCK_MODEL_ID = os.environ["AGENT_BEDROCK_MODEL_ID"]

class InvocationRequest(BaseModel):
    input: Dict[str, Any]

class InvocationResponse(BaseModel):
    output: Dict[str, Any]

app = FastAPI(title="Lawyer Agent Server", version="1.0.0")

def answer_with_lawyer(payload):
    """Answer questions using a KB and some other tools"""

    industry = payload["industry"]
    country = payload["country"]
    workload = payload["workload"]
    questions = payload["questions"]

    logger.debug(BEDROCK_MODEL_ID)

    QA_STR = ""

    LLM_QA_PROMPT_SELECTOR = get_lawyer_prompt_selector(lang="en")
    qa_prompt = LLM_QA_PROMPT_SELECTOR.get_prompt(BEDROCK_MODEL_ID)
    messages = qa_prompt.format_messages(
        industry=industry,
        country=country,
        workload=workload,
        json_schema=LawyerResponse.model_json_schema(),
        questions="\n\n".join(questions)
    )

    logger.debug("messages")
    logger.debug(messages)

    model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
    )

    lawyer_agent = Agent(
        model=model,
        system_prompt=messages[0].content,
        tools=[kb_answer, query_categorization]
    )

    try:
        agent_section_information = lawyer_agent(
            messages[1].content
        )

        logger.debug(agent_section_information)

        section_information_str = agent_section_information.message['content'][-1]['text']

        return {
            "status": 200,
            "content-type": "text",
            "timestamp": datetime.utcnow().isoformat(),
            "model": f"strands-agent-{BEDROCK_MODEL_ID}",
            "body": {
                "content":section_information_str
            }
        }

    except Exception as e:
        logger.error(traceback.format_exc())
        Exception("Agent processing failed: " + str(e))


@app.post("/invocations", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    try:

        logger.debug(f"Received request: {request}")

        #user_message = request.input.get("prompt", "")
        payload = request.input
        logger.debug(f"Received payload: {payload}")
        if "industry" not in payload or "country" not in payload or "workload" not in payload or "questions" not in payload:
            raise HTTPException(
                status_code=400, 
                detail=" Malformed input. Please check"
            )

        response = answer_with_lawyer(payload)

        return InvocationResponse(output=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")


@app.get("/ping")
async def ping():
    return {
    "status": "healthy",
    "time_of_last_update":datetime.now().timestamp()
    }
