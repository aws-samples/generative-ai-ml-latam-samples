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
import time
import boto3
import json
import logging
import queue
import heapq
import threading
import datetime
import traceback

from botocore.exceptions import ClientError
from ComplianceAnalysisTask import ComplianceAnalysis
from StatusEnum import ComplianceReportStatusEnum

logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'DEBUG').upper())
logger = logging.getLogger("MultiAgentComplianceAnalysis")

AUDITOR_AGENT_ARN = os.environ.get("AUDITOR_AGENT_ARN")
LAWYER_AGENT_ARN = os.environ.get("LAWYER_AGENT_ARN")
WRITER_AGENT_ARN = os.environ.get("WRITER_AGENT_ARN")
SQS_QUEUE_URL = os.environ.get("QUEUE_NAME")
JOBS_DYNAMOD_DB_NAME = os.environ.get("JOBS_DYNAMOD_DB_NAME")
S3_REPORTS_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")

DEFAULT_AGENT_QUALIFIER = "DEFAULT"

sqs_queue = boto3.resource('sqs').Queue(SQS_QUEUE_URL)
jobs_table = boto3.resource("dynamodb").Table(JOBS_DYNAMOD_DB_NAME)

s3 = boto3.client('s3')

analysis_queue = queue.SimpleQueue()
process_lock = threading.Lock()

def sleep(timeout, retry=3):
    def the_real_decorator(function):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < retry:
                try:
                    value = function(*args, **kwargs)
                    if value is None:
                        return
                except:
                    logger.info(f'Sleeping for {timeout} seconds')
                    time.sleep(timeout)
                    retries += 1
        return wrapper
    return the_real_decorator

def heapsort(iterable):
    h = []
    for value in iterable:
        heapq.heappush(h, value)
    return [heapq.heappop(h) for i in range(len(h))]

def get_job_by_id(
        job_id: str
):
    """
    Given an analysis job id, obtain its details
    @param analysis_job_id
    @return:
    """

    try:
        response = jobs_table.get_item(
            Key={
                "job_id": job_id
            }
        )

        if "Item" in response:
            return response["Item"]
        else:
            return ""
    except ClientError as ex:
        logger.error(f"Job {job_id} does not exist")
        raise ex


@sleep(20)
def poll_sqs():
    """Read incoming task from SQS"""

    awaiting_jobs = []

    logger.info("Pooling for jobs")

    messages = sqs_queue.receive_messages(
        MaxNumberOfMessages=5,
        VisibilityTimeout=30,
        WaitTimeSeconds=20,
    )

    logger.debug("Queue response")
    logger.debug(messages)

    if messages:
        for message in messages:

            logger.debug("The message")
            logger.debug(message)

            try:
                logger.debug(f"Received message: {message.body}")
                # Process the message here

                message_request = json.loads(message.body)

                logger.debug("The message request")
                logger.debug(message_request)

                job_id = message_request["job_id"]
                analysis_queue.put(job_id)
                #awaiting_jobs.append(job_id)

                message.delete()
            except Exception as e:
                logger.error("Caught exception but continuing without processing the job")
                logger.error(e)

        return awaiting_jobs
    else:
        logger.info("No messages in queue, waiting...")


def get_jobs_from_sqs():
    """Continuosly poll from SQS queue"""

    logger.info("SQS polling thread started")

    while True:
        awaiting_analysis = poll_sqs()

        for job_id in awaiting_analysis:
            logger.info(f"Enqueueing job: {job_id}")
            analysis_queue.put(job_id)


def do_compliance_analysis(
        job_id: str,
        report_template: dict,
        workload_country: str,
        workload_industry: str,
        workload_name: str,
        lawyer_agent_arn: str,
        writer_agent_arn: str,
        auditor_agent_arn: str,
        session_id: str
):

    compliance_analysis = ComplianceAnalysis(
        report_template=report_template,
        workload_country=workload_country,
        workload_industry=workload_industry,
        workload_name=workload_name,
        lawyer_agent_arn=lawyer_agent_arn,
        writer_agent_arn=writer_agent_arn,
        auditor_agent_arn=auditor_agent_arn,
        session_id=session_id
    )

    """Create the report from the report template"""

    #sections_compliance_report = []
    sorted_sections = []

    # Sort keys to generate report in order
    for section_name in report_template.keys():
        heapq.heappush(
            sorted_sections,
            (report_template[section_name]["order"], section_name)
        )

    sorted_sections = [element[1] for element in heapsort(sorted_sections)]
    logger.debug("Sections in order")
    logger.debug(sorted_sections)

    for section_name in sorted_sections:  # Uncomment for production
    #for section_name in sorted_sections[:MAX_SECTIONS]:

        """Generate compliance report for each section"""
        logger.info(f"Generating report for section: {section_name}")

        section_report_markdown = compliance_analysis.create_section_report(
            section_name=section_name,
            section_description=report_template[section_name]["description"],
            section_number=report_template[section_name]["order"],
            questions=report_template[section_name]["questions"],
        )

        # Save section to S3
        with open("./section.md", "w") as f:
            f.write(section_report_markdown)
            f.close()

        section_s3_key = f'{job_id}/report/{section_name}.md'
        s3.upload_file("./section.md", S3_REPORTS_BUCKET_NAME, section_s3_key)

        # Update DynamoDB Status
        jobs_table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #analysis_timestamp = :analysis_timestamp",
            ExpressionAttributeNames={"#analysis_timestamp": "analysis_timestamp"},
            ExpressionAttributeValues={":analysis_timestamp": int(datetime.datetime.now().timestamp())},
        )

        jobs_table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #analysis_section = :analysis_section",
            ExpressionAttributeNames={"#analysis_section": "analysis_section"},
            ExpressionAttributeValues={":analysis_section": section_name},
        )

        logger.info(f"Generated report for section {section_name}")
        logger.debug(section_report_markdown)

    return compliance_analysis.generate_compliance_report()


def process_analysis_jobs_by_section(
  job_id: str
):
    """Given a Job ID, retrieve its data and start the analysis job section by section"""

    process_lock.acquire_lock()

    logger.info(f"Processing job {job_id}")
    job_details = get_job_by_id(job_id)

    logger.debug("Analysis job details")
    logger.debug(job_details)

    jobs_table.update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET #status = :status",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={":status": ComplianceReportStatusEnum.QUESTION_ANSWERING.name},
    )

    logger.info("Starting compliance analysis")

    try:

        markdown_report = do_compliance_analysis(
            job_id=job_id,
            report_template=json.loads(job_details["report_with_questions"]),
            workload_country=job_details["country"],
            workload_industry=job_details["industry"],
            workload_name=job_details["workload"],
            lawyer_agent_arn=LAWYER_AGENT_ARN,
            writer_agent_arn=WRITER_AGENT_ARN,
            auditor_agent_arn=AUDITOR_AGENT_ARN,
            session_id="fgyugifsfjaigayogsyfisgbfiuasinsaiuhouif"
        )

        logger.info("Completed compliance analysis")
        logger.debug("the report")
        logger.debug(markdown_report)

        # Upload file to S3
        with open("./report.md", "w") as f:
            f.write(markdown_report)

        report_s3_key = f'{job_id}/report/compliance_report.md'
        s3.upload_file("./report.md", S3_REPORTS_BUCKET_NAME, report_s3_key)

        # Update status in DynamoDB
        jobs_table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #report_s3_key = :report_s3_key",
            ExpressionAttributeNames={"#report_s3_key": "report_s3_key"},
            ExpressionAttributeValues={":report_s3_key": report_s3_key},
        )

        jobs_table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": ComplianceReportStatusEnum.SUCCESS.name},
        )

    except Exception as e:
        logger.error("Error while processing job")
        logger.error(traceback.format_exc())
        jobs_table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": ComplianceReportStatusEnum.ERROR.name},
        )
    finally:
        process_lock.release_lock()


def process_analysis_jobs(
  job_id: str
):
    """Given a Job ID, retrieve its data and start the analysis job"""

    process_lock.acquire_lock()

    logger.info(f"Processing job {job_id}")
    job_details = get_job_by_id(job_id)

    logger.debug("Analysis job details")
    logger.debug(job_details)

    compliance_analysis = ComplianceAnalysis(
        report_template=json.loads(job_details["report_with_questions"]),
        workload_country=job_details["country"],
        workload_industry=job_details["industry"],
        workload_name=job_details["workload"],
        lawyer_agent_arn=LAWYER_AGENT_ARN,
        writer_agent_arn=WRITER_AGENT_ARN,
        auditor_agent_arn=AUDITOR_AGENT_ARN,
        session_id="fgyugifsfjaigayogsyfisgbfiuasinsaiuhouif"
    )

    jobs_table.update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET #status = :status",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={":status": ComplianceReportStatusEnum.QUESTION_ANSWERING.name},
    )

    logger.info("Starting compliance analysis")
    compliance_analysis.do_compliance_analysis()

    logger.info("Completed compliance analysis")
    logger.debug("the report")
    logger.debug(compliance_analysis.compliance_report_markdown)

    # Upload file to S3
    with open("./report.md", "w") as f:
        f.write(compliance_analysis.compliance_report_markdown)

    report_s3_key = f'{job_details["job_id"]}/report/compliance_report.md'
    s3.upload_file("./report.md", S3_REPORTS_BUCKET_NAME, report_s3_key)

    # Update status in DynamoDB
    jobs_table.update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET #report_s3_key = :report_s3_key",
        ExpressionAttributeNames={"#report_s3_key": "report_s3_key"},
        ExpressionAttributeValues={":report_s3_key": report_s3_key},
    )

    jobs_table.update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET #status = :status",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={":status": ComplianceReportStatusEnum.SUCCESS.name},
    )

    process_lock.release_lock()


if __name__ == "__main__":

    logger.info("Inside the fargate job")

    logger.info(AUDITOR_AGENT_ARN)
    logger.info(LAWYER_AGENT_ARN)
    logger.info(WRITER_AGENT_ARN)
    logger.info(SQS_QUEUE_URL)
    logger.info(JOBS_DYNAMOD_DB_NAME)

    logger.info("Starting queue consumer")
    #sqs_queue_consumer = threading.Thread(target=get_jobs_from_sqs)
    #sqs_queue_consumer.start()
    #sqs_queue_consumer.join()

    #Read from AnalysisQueue
    while True:

        #Poll SQS
        poll_sqs()

        logger.info("Analysis queue")
        logger.debug(analysis_queue)

        if not analysis_queue.empty():
            job_id = analysis_queue.get()
            logger.info("Found job waiting")
            logger.info(job_id)

            compliance_analysis = threading.Thread(target=process_analysis_jobs_by_section, args=[job_id])
            compliance_analysis.start()
            compliance_analysis.join()

        else:
            logger.info("Queue is empty")



