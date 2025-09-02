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


import re
import boto3
import json
import logging
import heapq

from retrying import retry
from botocore.config import Config

logger = logging.getLogger("MultiAgentComplianceAnalysis")

DEFAULT_AGENT_QUALIFIER = "DEFAULT"


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

def heapsort(iterable):
    h = []
    for value in iterable:
        heapq.heappush(h, value)
    return [heapq.heappop(h) for i in range(len(h))]

class ComplianceAnalysis:
    """A class to execute the compliance analysis"""

    def __init__(
            self,
            report_template: dict,
            workload_country: str,
            workload_industry: str,
            workload_name: str,
            lawyer_agent_arn: str,
            writer_agent_arn: str,
            auditor_agent_arn: str,
            session_id: str
    ):

        self.report_template = report_template
        self.compliance_report_by_section = {}
        self.ordered_report_sections = []
        self.sorted_report_str = ""
        self.compliance_report_markdown = ""

        if lawyer_agent_arn and writer_agent_arn and auditor_agent_arn:

            self.lawyer_agent_arn = lawyer_agent_arn
            self.writer_agent_arn = writer_agent_arn
            self.auditor_agent_arn = auditor_agent_arn

        else:
            logger.error("Agent ARN can not be empty value")
            raise Exception("Agent ARN can not be empty value")

        if workload_country and workload_industry and workload_name:

            self.workload_country = workload_country
            self.workload_industry = workload_industry
            self.workload_name = workload_name

        else:
            logger.error("Missing required workload details")
            raise Exception("Missing required workload details")

        if session_id:
            self.session_id = session_id
        else:
            logger.error("Session Id can not be empty value")
            raise Exception("Session Id can not be empty value")


    def create_markdown_index(self):

        # Extract headings using regex for # and ## only
        h1_pattern = re.compile(r'^# (.+)', re.MULTILINE)
        h2_pattern = re.compile(r'^## (.+)', re.MULTILINE)

        # Find all h1 and h2 headings
        h1_headings_with_positions = [(match.group(1), match.start(), 1)
                                      for match in h1_pattern.finditer(self.sorted_report_str)]
        h2_headings_with_positions = [(match.group(1), match.start(), 2)
                                      for match in h2_pattern.finditer(self.sorted_report_str)]

        ordered_headings = []

        i, j = 0, 0

        # Merge two sorted arrays
        while i < len(h1_headings_with_positions) or j < len(h2_headings_with_positions):

            if i == len(h1_headings_with_positions):
                ordered_headings.extend(h2_headings_with_positions[j:])
                break
            if j == len(h2_headings_with_positions):
                ordered_headings.extend(h1_headings_with_positions[i:])
                break

            if h1_headings_with_positions[i][1] < h2_headings_with_positions[j][1]:
                ordered_headings.append(h1_headings_with_positions[i])
                i += 1
            else:
                ordered_headings.append(h2_headings_with_positions[j])
                j += 1

        logger.debug(h1_headings_with_positions)
        logger.debug(h2_headings_with_positions)
        logger.debug(ordered_headings)

        # Create index in markdown format
        index = "# Table of Contents\n\n"

        for heading, _, level in ordered_headings:

            if level == 1:
                # Create a proper markdown link anchor
                # Convert heading to lowercase, replace spaces with hyphens, remove punctuation

                anchor = heading.lower()
                anchor = re.sub(r'[^\w\s-]', '', anchor)  # Remove special characters
                anchor = re.sub(r'\s+', '-', anchor)  # Replace spaces with hyphens

                # Add the h1 heading with proper indentation
                index += f"- [{heading}](#{anchor})\n"
            if level == 2:
                # Create a proper markdown link anchor
                # Convert heading to lowercase, replace spaces with hyphens, remove punctuation

                anchor = heading.lower()
                anchor = re.sub(r'[^\w\s-]', '', anchor)  # Remove special characters
                anchor = re.sub(r'\s+', '-', anchor)  # Replace spaces with hyphens

                # Add the h2 heading with proper indentation
                index += f"  - [{heading}](#{anchor})\n"

        return index


    @retry(wait_exponential_multiplier=10000, wait_exponential_max=900000, stop_max_attempt_number=6,
           retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
    def compliance_assessment(
            self,
            section_name: str,
            section_description: str,
            section_report_draft: str,
            qa_set: str,
    ):
        """Given a set of questions and answers, and a draft of a report assess the compliance of the workload according to regulation"""

        logger.info("Invoking agent with:")
        logger.info(self.auditor_agent_arn)
        logger.info(DEFAULT_AGENT_QUALIFIER)

        # Invoke the AUDITOR agent
        auditor_agent_response = agent_core_client.invoke_agent_runtime(
            agentRuntimeArn=self.auditor_agent_arn,
            qualifier=DEFAULT_AGENT_QUALIFIER,
            runtimeSessionId=self.session_id,
            payload=json.dumps({
                "input":{
                    "country": self.workload_country,
                    "industry": self.workload_industry,
                    "workload": self.workload_name,
                    "section": section_name,
                    "description": section_description,
                    "markdown_report": section_report_draft,
                    "questions": qa_set
                }
            })
        )

        if "application/json" in auditor_agent_response.get("contentType", ""):
            for line in auditor_agent_response["response"].iter_lines(chunk_size=1):
                if line:
                    auditor_response = json.loads(line.decode("utf-8"))["output"]
                    logger.debug(auditor_response)

                    if auditor_response["status"] == 200:
                        if auditor_response["content-type"] == "application/json":
                            return auditor_response["body"]["content"]
                    else:
                        logger.debug("Agent server error")
                        logger.debug(auditor_response["body"]["content"])
                        raise BedrockRetryableError("Agent server error. Retrying")


    @retry(wait_exponential_multiplier=10000, wait_exponential_max=900000, stop_max_attempt_number=6,
           retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
    def answer_questions(
            self,
            questions: list[str],
    ):
        """Given a set of questions, use the lawyer agent to answer them"""

        qa_set_str = ""

        logger.info("Invoking agent with:")
        logger.info(self.lawyer_agent_arn)
        logger.info(DEFAULT_AGENT_QUALIFIER)

        # Invoke the LAWYER agent
        lawyer_agent_response = agent_core_client.invoke_agent_runtime(
            agentRuntimeArn=self.lawyer_agent_arn,
            qualifier=DEFAULT_AGENT_QUALIFIER,
            runtimeSessionId=self.session_id,
            payload=json.dumps({
                "input":{
                    "country": self.workload_country,
                    "industry": self.workload_industry,
                    "workload": self.workload_name,
                    "questions": questions
                }
            })
        )

        logger.debug("Lawyer responded")

        if "application/json" in lawyer_agent_response.get("contentType", ""):
            for line in lawyer_agent_response["response"].iter_lines(chunk_size=1):
                if line:
                    lawyer_response = json.loads(line.decode("utf-8"))["output"]
                    logger.debug(lawyer_response)
                    logger.debug(type(lawyer_response))

                    if lawyer_response["status"] == 200:
                        if lawyer_response["content-type"] == "application/json":
                            for qa in lawyer_response["body"]["content"]:
                                qa_set_str = qa_set_str + f"<qa_pair>Question:{qa["question"]} Answer:{qa["answer"]}</qa_pair>\n\n"
                            return qa_set_str

                        elif lawyer_response["content-type"] == "text":
                            return lawyer_response["body"]["content"]
                    else:
                        logger.error("Agent server error")
                        logger.error(lawyer_response["body"]["content"])
                        raise BedrockRetryableError("Agent server error. Retrying")


    @retry(wait_exponential_multiplier=10000, wait_exponential_max=900000, stop_max_attempt_number=6,
           retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
    def write_section_report(
            self,
            section_name: str,
            section_description: str,
            section_number: int,
            qa_set: str
    ):
        """Given a set of Q&A, use the writer agent to draft a report for the section"""

        logger.info("Invoking agent with:")
        logger.info(self.writer_agent_arn)
        logger.info(DEFAULT_AGENT_QUALIFIER)

        # Invoke the WRITER agent
        writer_agent_response = agent_core_client.invoke_agent_runtime(
            agentRuntimeArn=self.writer_agent_arn,
            qualifier=DEFAULT_AGENT_QUALIFIER,
            runtimeSessionId=self.session_id,
            payload=json.dumps({
                "input":{
                    "country": self.workload_country,
                    "industry": self.workload_industry,
                    "workload": self.workload_name,
                    "section": section_name,
                    "description": section_description,
                    "section_number": section_number,
                    "questions": qa_set
                }
            })
        )

        if "application/json" in writer_agent_response.get("contentType", ""):
            for line in writer_agent_response["response"].iter_lines(chunk_size=1):
                if line:
                    writer_response = json.loads(line.decode("utf-8"))["output"]
                    logger.debug(writer_response)
                    logger.debug(type(writer_response))

                    if writer_response["status"] == 200:
                        if writer_response["content-type"] == "text":
                            return writer_response["body"]["content"]
                    else:
                        logger.error("Agent server error")
                        logger.error(writer_response["body"]["content"])
                        raise BedrockRetryableError("Agent server error. Retrying")


    def create_section_report(
            self,
            section_name: str,
            section_description: str,
            section_number: int,
            questions: list[str]
    ):

        """Feedback loop for creating a section report using the interaction between """

        MAX_ASSESSMENT_TRIALS = 2 #Adjust for production to 3-5 trials depending on budget or accuracy requirements
        qa_str = ""

        assessment_complete = False
        assessment_trials = 0

        # First answer the set of questions from the template using the lawyer
        questions_answers = self.answer_questions(
            questions=questions,
        )
        logger.debug("The QA set")
        logger.debug(questions_answers)

        qa_str = qa_str + "\n\n" + questions_answers

        markdown_report = self.write_section_report(
            section_name=section_name,
            section_description=section_description,
            section_number=section_number,
            qa_set=qa_str,
        )
        logger.debug("The markdown report")
        logger.debug(markdown_report)

        while not assessment_complete and assessment_trials < MAX_ASSESSMENT_TRIALS:
            """Team working loop"""

            logger.info(f"Assessment not complete for section {section_name}, running the assessment. Trial number {assessment_trials}")

            assessment = self.compliance_assessment(
                section_name=section_name,
                section_description=section_description,
                section_report_draft=markdown_report,
                qa_set=qa_str,
            )
            logger.debug("The assessment")
            logger.debug(assessment)

            assessment_complete = assessment["is_compliant"]

            if not assessment_complete:
                questions_answers = self.answer_questions(
                    questions=assessment["follow_up_questions"],
                )
                logger.debug("The QA set")
                logger.debug(questions_answers)

                qa_str = qa_str + "\n\n" + questions_answers

                markdown_report = self.write_section_report(
                    section_name=section_name,
                    section_description=section_description,
                    section_number=section_number,
                    qa_set=qa_str,
                )
                logger.debug("The markdown report")
                logger.debug(markdown_report)

            assessment_trials += 1

        self.compliance_report_by_section[section_name] = markdown_report

        heapq.heappush(
            self.ordered_report_sections,
            (self.report_template[section_name]["order"], markdown_report)
        )

        return markdown_report


    def generate_compliance_report(
            self
    ):
        """Given the report sections, create a final compliance report aided by LLMs"""

        markdown_sections = [element[1] for element in heapsort(self.ordered_report_sections)]
        self.sorted_report_str = "\n\n".join(markdown_sections)

        table_of_contents = self.create_markdown_index()

        self.compliance_report_markdown = "# Compliance Report\n\n" + "\n\n" + table_of_contents + self.sorted_report_str

        return self.compliance_report_markdown


    def do_compliance_analysis(
            self
    ):
        """Create the report from the report template"""

        sections_compliance_report = []

        for section_name in self.report_template.keys():
            """Generate compliance report for each section"""
            logger.info(f"Generating report for section: {section_name}")

            section_report_markdown = self.create_section_report(
                section_name=section_name,
                section_description=self.report_template[section_name]["description"],
                section_number=int(self.report_template[section_name]["order"]),
                questions=self.report_template[section_name]["questions"],
            )

            logger.info(f"Generated report for section {section_name}")
            logger.debug(section_report_markdown)

        return self.generate_compliance_report()