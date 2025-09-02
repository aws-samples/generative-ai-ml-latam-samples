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

import boto3
import json
import logging
from retrying import retry

from botocore.config import Config

logger = logging.getLogger(__name__)

AUDITOR_AGENT_ARN = os.environ.get("AUDITOR_AGENT_ARN")
LAWYER_AGENT_ARN = os.environ.get("LAWYER_AGENT_ARN")
WRITER_AGENT_ARN = os.environ.get("WRITER_AGENT_ARN")
SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL")

DEFAULT_AGENT_QUALIFIER = "DEFAULT"

sample_sections = {
    "Verificación de identidad": {
			"description": "Procedimientos y medidas para la verificación de la identidad de los clientes",
			"questions": [
				"¿Qué medidas de verificación se implementan para asegurar la identidad de los clientes en estos servicios?",
				"¿Qué mecanismos técnicos se utilizan para la verificación de la información biométrica de los clientes?",
				"¿Cómo se asegura la autenticación de la huella dactilar obtenida directamente del cliente?",
				"¿Cómo se gestionan los casos en los que no se puede obtener la huella dactilar de un cliente?",
				"¿Qué proceso se sigue para la verificación de documentos de identidad en operaciones de retiros y transferencias?",
				"¿Qué documentos se requieren para retiros y transferencias por montos específicos?",
				"¿Cómo se gestionan las operaciones con clientes que no pueden presentar su credencial para votar?",
				"¿Qué pasos se siguen para la verificación de pasaportes y documentos migratorios?",
				"¿Cómo se asegura la coincidencia de datos entre diferentes documentos de identidad presentados por un cliente?",
				"¿Qué procedimiento se sigue para la verificación de matrículas consulares?",
				"¿Cómo se gestionan las operaciones con clientes cuyas matrículas consulares no pueden ser verificadas en línea?",
				"¿Qué procedimientos se siguen para la autorización de documentos de identificación alternativos y acciones de verificación?"
			],
			"order": 18
		}
}

class BedrockRetryableError(Exception):
    """Class to identify a Bedrock throttling error"""

    def __init__(self, msg):
        super().__init__(self)

        self.message = msg

# Initialize the Bedrock AgentCore client
agent_core_client = boto3.client(
    'bedrock-agentcore',
    region_name="us-east-1",
    config=Config(
            connect_timeout=180,
            read_timeout=180,
            retries={
                "max_attempts": 50,
                "mode": "adaptive",
            },
        )
)

@retry(wait_exponential_multiplier=10000, wait_exponential_max=900000, stop_max_attempt_number=6,
       retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
def compliance_assessment(
        country: str,
        industry: str,
        workload_name: str,
        section_name: str,
        section_description: str,
        section_report_draft:str,
        qa_set: str,
        session_id: str
):
    """Given a set of questions and answers, and a draft of a report assess the compliance of the workload according to regulation"""

    print("Invoking agent with:")
    print(LAWYER_AGENT_ARN)
    print(DEFAULT_AGENT_QUALIFIER)

    # Invoke the AUDITOR agent
    auditor_agent_response = agent_core_client.invoke_agent_runtime(
        agentRuntimeArn=AUDITOR_AGENT_ARN,
        qualifier=DEFAULT_AGENT_QUALIFIER,
        runtimeSessionId=session_id,
        payload=json.dumps({
            "country": country,
            "industry": industry,
            "workload": workload_name,
            "section": section_name,
            "description": section_description,
            "markdown_report" : section_report_draft,
            "questions": qa_set
        })
    )

    if "application/json" in auditor_agent_response.get("contentType", ""):
        for line in auditor_agent_response["response"].iter_lines(chunk_size=1):
            if line:
                auditor_response = json.loads(line.decode("utf-8"))
                print(auditor_response)

                if auditor_response["status"] == 200:
                    if auditor_response["content-type"] == "application/json":
                        return auditor_response["body"]["content"]
                else:
                    print("Agent server error")
                    print(auditor_response["body"]["content"])
                    raise BedrockRetryableError("Agent server error. Retrying")


@retry(wait_exponential_multiplier=10000, wait_exponential_max=900000, stop_max_attempt_number=6,
       retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
def answer_questions(
        country: str,
        industry: str,
        workload_name: str,
        questions: list[str],
        session_id: str
):
    """Given a set of questions, use the lawyer agent to answer them"""

    qa_set_str = ""

    print("Invoking agent with:")
    print(LAWYER_AGENT_ARN)
    print(DEFAULT_AGENT_QUALIFIER)

    # Invoke the LAWYER agent
    lawyer_agent_response = agent_core_client.invoke_agent_runtime(
        agentRuntimeArn=LAWYER_AGENT_ARN,
        qualifier=DEFAULT_AGENT_QUALIFIER,
        runtimeSessionId=session_id,
        payload=json.dumps({
            "country": country,
            "industry": industry,
            "workload": workload_name,
            "questions": questions
        })
    )

    print("Lawyer responded")

    if "application/json" in lawyer_agent_response.get("contentType", ""):
        for line in lawyer_agent_response["response"].iter_lines(chunk_size=1):
            if line:
                lawyer_response = json.loads(line.decode("utf-8"))
                print(lawyer_response)
                print(type(lawyer_response))

                if lawyer_response["status"] == 200:
                    if lawyer_response["content-type"] == "application/json":
                        for qa in lawyer_response["body"]["content"]:
                            qa_set_str = qa_set_str + f"<qa_pair>Question:{qa["question"]} Answer:{qa["answer"]}</qa_pair>\n\n"
                        return qa_set_str

                    elif lawyer_response["content-type"] == "text":
                        return lawyer_response["body"]["content"]
                else:
                    print("Agent server error")
                    print(lawyer_response["body"]["content"])
                    raise BedrockRetryableError("Agent server error. Retrying")


@retry(wait_exponential_multiplier=10000, wait_exponential_max=900000, stop_max_attempt_number=6,
       retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
def write_section_report(
        country: str,
        industry: str,
        workload_name: str,
        section_name: str,
        section_description: str,
        qa_set: str,
        session_id: str
):
    """Given a set of Q&A, use the writer agent to draft a report for the section"""

    print("Invoking agent with:")
    print(WRITER_AGENT_ARN)
    print(DEFAULT_AGENT_QUALIFIER)

    # Invoke the WRITER agent
    writer_agent_response = agent_core_client.invoke_agent_runtime(
        agentRuntimeArn=WRITER_AGENT_ARN,
        qualifier=DEFAULT_AGENT_QUALIFIER,
        runtimeSessionId=session_id,
        payload=json.dumps({
            "country": country,
            "industry": industry,
            "workload": workload_name,
            "section": section_name,
            "description": section_description,
            "questions": qa_set
        })
    )

    if "application/json" in writer_agent_response.get("contentType", ""):
        for line in writer_agent_response["response"].iter_lines(chunk_size=1):
            if line:
                writer_response = json.loads(line.decode("utf-8"))
                print(writer_response)
                print(type(writer_response))

                if writer_response["status"] == 200:
                    if writer_response["content-type"] == "text":
                        return writer_response["body"]["content"]
                else:
                    print("Agent server error")
                    print(writer_response["body"]["content"])
                    raise BedrockRetryableError("Agent server error. Retrying")


def create_section_report(
        country: str,
        industry: str,
        workload_name: str,
        section_name: str,
        section_description: str,
        questions: list[str]
):

    """Feedback loop for creating a section report using the interaction between """

    MAX_ASSESSMENT_TRIALS = 3
    qa_str = ""

    sessionId = 'fgyugifsfjaigayogsyfisgbfiuasinsaiuhouif'

    assessment_complete = False
    assessment_trials = 0

    #First answer the set of questions from the template using the lawyer
    questions_answers = answer_questions(
        country=country,
        industry=industry,
        workload_name=workload_name,
        questions=questions,
        session_id=sessionId
    )
    print("The QA set")
    print(questions_answers)

    markdown_report = write_section_report(
        country=country,
        industry=industry,
        workload_name=workload_name,
        section_name=section_name,
        section_description=section_description,
        qa_set=qa_str,
        session_id=sessionId
    )
    print("The markdown report")
    print(markdown_report)

    while not assessment_complete and assessment_trials <= MAX_ASSESSMENT_TRIALS:
        """Team working loop"""

        print("Assessment not complete, running the assessment")

        assessment = compliance_assessment(
            country=country,
            industry=industry,
            workload_name=workload_name,
            section_name=section_name,
            section_description=section_description,
            section_report_draft=markdown_report,
            qa_set=qa_str,
            session_id=sessionId
        )
        print("The assessment")
        print(assessment)

        assessment_complete = assessment["is_compliant"]

        if not assessment_complete:

            questions_answers = answer_questions(
                country=country,
                industry=industry,
                workload_name=workload_name,
                questions=assessment["follow_up_questions"],
                session_id=sessionId
            )
            print("The QA set")
            print(questions_answers)

            markdown_report = write_section_report(
                country=country,
                industry=industry,
                workload_name=workload_name,
                section_name=section_name,
                section_description=section_description,
                qa_set=qa_str,
                session_id=sessionId
            )
            print("The markdown report")
            print(markdown_report)

        assessment_trials += 1

    return markdown_report



if __name__ == "__main__":

    for section_name in sample_sections.keys():

        print(f"Generating report for section: {section_name}")

        section_report = create_section_report(
            country="mexico",
            industry="servicios financieros",
            workload_name="core bancario",
            section_name=section_name,
            section_description=sample_sections[section_name]["description"],
            questions=sample_sections[section_name]["questions"],
        )
