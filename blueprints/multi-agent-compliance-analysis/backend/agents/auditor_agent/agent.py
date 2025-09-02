import os
import json
import logging
import traceback

from strands import Agent, tool
from strands.models import BedrockModel

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from prompt_selector.generate_auditor_prompt import get_auditor_prompt_selector
from structured_output.AuditorResponse import AuditorResponse

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

app = FastAPI(title="Auditor Agent Server", version="1.0.0")


@app.post("/invocations", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    """Using a set of Q&A and a report from those Q&A determine if the process is compliant or not"""

    logger.debug(f"Received request: {request}")

    #user_message = request.input.get("prompt", "")
    payload = request.input
    logger.debug(f"Received payload: {payload}")

    industry = payload["industry"]
    country = payload["country"]
    workload = payload["workload"]
    section = payload["section"]
    description = payload["description"]
    markdown_report = payload["markdown_report"]
    questions = payload["questions"]

    LLM_PERFORM_AUDIT_ASSESSMENT_PROMPT_SELECTOR = get_auditor_prompt_selector(lang="en")
    audit_assessment_prompt = LLM_PERFORM_AUDIT_ASSESSMENT_PROMPT_SELECTOR.get_prompt(BEDROCK_MODEL_ID)
    messages = audit_assessment_prompt.format_messages(
        industry=industry,
        country=country,
        workload=workload,
        section_name=section,
        section_description=description,
        compliance_report=markdown_report,
        questions=questions
    )

    logger.debug("messages")
    logger.debug(messages)

    model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        temperature=0.2
    )

    auditor_agent = Agent(
        model=model,
        system_prompt=messages[0].content
    )

    try:

        auditor_compliance_assessment = auditor_agent(messages[1].content)

        auditor_compliance_assessment_str = auditor_compliance_assessment.message['content'][-1]['text']

        logger.debug("Assessment as text")
        logger.debug(auditor_compliance_assessment_str)

        auditor_compliance_assessment = auditor_agent.structured_output(
            AuditorResponse,
            auditor_compliance_assessment_str
        )

        logger.debug("Structured assessment")
        logger.debug(auditor_compliance_assessment)

        response = {
            "status": 200,
            "content-type": "application/json",
            "body": {
                "content": auditor_compliance_assessment.model_dump()
            }
        }

        return InvocationResponse(output=response)

    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")


@app.get("/ping")
async def ping():
    return {
    "status": "healthy",
    "time_of_last_update":datetime.now().timestamp()
    }