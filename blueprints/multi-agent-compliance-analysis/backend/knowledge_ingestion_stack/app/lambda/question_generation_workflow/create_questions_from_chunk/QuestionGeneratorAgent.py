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

import boto3

from botocore.exceptions import ClientError
from botocore.config import Config

from retrying import retry

from enum import Enum
from aws_lambda_powertools import Logger

from langchain_aws import ChatBedrockConverse

from prompts.question_generation_with_reflexion.generate_questions_prompt import get_questions_prompt_selector, extract_questions_prompt_selector
from prompts.question_generation_with_reflexion.evaluate_questions_prompt import get_question_eval_prompt_selector, extract_q_evaluations_prompt_selector
from prompts.question_generation_with_reflexion.reflect_questions_prompt import get_reflexion_prompt_selector
from structured_output.questions import DocumentQuestions, QEvals, QuestionEvaluation, QuestionGenerationOutput

STRUCTURED_OUTPUT_MODEL_TEMP = 0.2
ACTION_MODEL_TEMP = 0.6
EVAL_MODEL_TEMP = 0.6
REFLEXION_MODEL_TEMP = 0.6

class StopReason(Enum):
    IN_PROGRESS = 0
    MAX_TRIALS = 1
    SCORE_REACHED = 2
    CHUNK_NOT_RELEVANT = 3


class BedrockRetryableError(Exception):
    """Class to identify a Bedrock throttling error"""

    def __init__(self, msg):
        super().__init__(self)

        self.message = msg


class QuestionGenerationSelfReflexionAgent():

    def __init__(
        self,
        industry: str,
        country: str,
        workload: str,
        gold_standard_questions: list[str],
        expected_score: float,
        max_trials: int,
        action_model_id: str,
        logger: Logger,
        bedrock_region: str,
        reflexion_model_id: str = "",
        evaluator_model_id: str = "",
        structured_output_model_id: str = "us.amazon.nova-lite-v1:0"
    ):

        self.stop_reason = StopReason.IN_PROGRESS
        self.industry = industry
        self.country = country
        self.workload = workload
        self.expected_score = expected_score
        self.chunk_topic_related = False
        self.current_score = 0
        self.max_trials = max_trials
        self.memory = []
        self.current_feedback = ""
        self.current_qa_str = ""
        self.current_qa = []
        self.gold_standard_questions_str = "\n".join(gold_standard_questions)
        self.action_model_id = action_model_id
        self.reflexion_model_id = reflexion_model_id
        self.evaluator_model_id = evaluator_model_id
        self.structured_output_model_id = structured_output_model_id
        self.logger = logger

        self.logger.info("Parameters")
        self.logger.info(f"Industry :{self.industry}")
        self.logger.info(f"Workload :{self.workload}")
        self.logger.info(f"Country :{self.country}")
        self.logger.info(f"Current feedback: {self.current_feedback}")
        self.logger.info(f"Current Questions: {self.current_qa_str}")
        self.logger.info(f"Gold standard Questions: {self.gold_standard_questions_str}")

        # Initialize Bedrock client
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=bedrock_region,
            config=Config(
                connect_timeout=180,
                read_timeout=180,
                retries={
                    "max_attempts": 20,
                    "mode": "adaptive",
                },
            )
        )

        """
        self.structured_output_model = ChatBedrockConverse(
            model=self.structured_output_model_id,
            temperature=0.2,
            max_tokens=5000,
            # other params...
        )

        self.action_model = ChatBedrockConverse(
            model=self.action_model_id,
            temperature=0.6,
            max_tokens=3000,
            # other params...
        )

        self.reflexion_model = ChatBedrockConverse(
            model=self.reflexion_model_id if self.reflexion_model_id else self.action_model_id,
            temperature=0.6,
            max_tokens=3000,
            # other params...
        ) if reflexion_model_id else self.action_model

        self.evaluator_model = ChatBedrockConverse(
            model=self.evaluator_model_id if self.evaluator_model_id else self.action_model_id,
            temperature=0.6,
            max_tokens=5000,
            # other params...
        ) if evaluator_model_id else self.action_model
        """


    @retry(wait_exponential_multiplier=10000, wait_exponential_max=900000, stop_max_attempt_number=9,
           retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
    def get_last_question_batch(
        self
    ):

        global STRUCTURED_OUTPUT_MODEL_TEMP
        """This function returns the questions of the last execution"""
        try:

            structured_output_llm = ChatBedrockConverse(
                model=self.structured_output_model_id,
                temperature=STRUCTURED_OUTPUT_MODEL_TEMP if STRUCTURED_OUTPUT_MODEL_TEMP<1 else 1,
                max_tokens=8000,
                # other params...
            )

            if self.current_qa_str:

                ############----------Chain action---------############
                LLM_EXTRACT_QUESTIONS_PROMPT_SELECTOR = extract_questions_prompt_selector(lang="en")
                extract_questions_prompt = LLM_EXTRACT_QUESTIONS_PROMPT_SELECTOR.get_prompt(self.structured_output_model_id)
                extract_questions_chain = extract_questions_prompt | structured_output_llm.with_structured_output(DocumentQuestions)

                questions = extract_questions_chain.invoke(self.current_qa_str)

                print("questions")
                print(questions)

                self.chunk_topic_related = questions.is_text_relevant

                if self.chunk_topic_related:
                    self.current_qa = questions.questions
                else:
                    return self.chunk_topic_related, []
            else:
                return self.chunk_topic_related, []

            return self.chunk_topic_related, self.current_qa

        except ClientError as exc:
            if exc.response['Error']['Code'] == 'ThrottlingException':
                self.logger.error("Bedrock throttling. To try again")
                raise BedrockRetryableError(str(exc))
            elif exc.response['Error']['Code'] == 'ModelTimeoutException':
                self.logger.error("Bedrock ModelTimeoutException. To try again")
                raise BedrockRetryableError(str(exc))
            elif exc.response['Error']['Code'] == 'ModelErrorException':
                STRUCTURED_OUTPUT_MODEL_TEMP = STRUCTURED_OUTPUT_MODEL_TEMP + 0.1
                self.logger.error("Bedrock ModelErrorException. To try again")
                raise BedrockRetryableError(str(exc))
            else:
                raise
        except self.bedrock_runtime.exceptions.ThrottlingException as throttlingExc:
            self.logger.error("Bedrock ThrottlingException. To try again")
            raise BedrockRetryableError(str(throttlingExc))
        except self.bedrock_runtime.exceptions.ModelTimeoutException as timeoutExc:
            self.logger.error("Bedrock ModelTimeoutException. To try again")
            raise BedrockRetryableError(str(timeoutExc))
        except self.bedrock_runtime.exceptions.ModelErrorException as modelErrExc:
            STRUCTURED_OUTPUT_MODEL_TEMP = STRUCTURED_OUTPUT_MODEL_TEMP+0.1
            self.logger.error("Bedrock ModelErrorException. To try again")
            raise BedrockRetryableError(str(modelErrExc))
        except Exception as e:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            self.logger.error(message)
            raise


    @retry(wait_exponential_multiplier=10000, wait_exponential_max=900000, stop_max_attempt_number=9,
           retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
    def get_evals(
        self,
        text_evaluations:str
    ):

        global STRUCTURED_OUTPUT_MODEL_TEMP

        try:

            structured_output_llm = ChatBedrockConverse(
                model=self.structured_output_model_id,
                temperature=STRUCTURED_OUTPUT_MODEL_TEMP if STRUCTURED_OUTPUT_MODEL_TEMP<1 else 1,
                max_tokens=8000,
                # other params...
            )

            """This function returns the evaluations in a structured way"""
            ############----------Chain action---------############
            LLM_EXTRACT_EVALS_PROMPT_SELECTOR = extract_q_evaluations_prompt_selector(lang="en")
            extract_evals_prompt = LLM_EXTRACT_EVALS_PROMPT_SELECTOR.get_prompt(self.structured_output_model_id)
            extract_evals_chain = extract_evals_prompt | structured_output_llm.with_structured_output(QEvals)

            q_evals = extract_evals_chain.invoke(text_evaluations)

            return q_evals
        except ClientError as exc:
            if exc.response['Error']['Code'] == 'ThrottlingException':
                self.logger.error("Bedrock throttling. To try again")
                raise BedrockRetryableError(str(exc))
            elif exc.response['Error']['Code'] == 'ModelTimeoutException':
                self.logger.error("Bedrock ModelTimeoutException. To try again")
                raise BedrockRetryableError(str(exc))
            elif exc.response['Error']['Code'] == 'ModelErrorException':
                STRUCTURED_OUTPUT_MODEL_TEMP = STRUCTURED_OUTPUT_MODEL_TEMP + 0.1
                self.logger.error("Bedrock ModelErrorException. To try again")
                raise BedrockRetryableError(str(exc))
            else:
                raise
        except self.bedrock_runtime.exceptions.ThrottlingException as throttlingExc:
            self.logger.error("Bedrock ThrottlingException. To try again")
            raise BedrockRetryableError(str(throttlingExc))
        except self.bedrock_runtime.exceptions.ModelTimeoutException as timeoutExc:
            self.logger.error("Bedrock ModelTimeoutException. To try again")
            raise BedrockRetryableError(str(timeoutExc))
        except self.bedrock_runtime.exceptions.ModelErrorException as modelErrExc:
            STRUCTURED_OUTPUT_MODEL_TEMP = STRUCTURED_OUTPUT_MODEL_TEMP+0.1
            self.logger.error("Bedrock ModelErrorException. To try again")
            raise BedrockRetryableError(str(modelErrExc))
        except Exception as e:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            self.logger.error(message)
            raise


    @retry(wait_exponential_multiplier=10000, wait_exponential_max=900000, stop_max_attempt_number=9,
           retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
    def perform_task(
        self,
        n_questions:str,
        regulation_portion:str
    ):

        global ACTION_MODEL_TEMP

        try:

            action_llm = ChatBedrockConverse(
                model=self.action_model_id,
                temperature=ACTION_MODEL_TEMP if ACTION_MODEL_TEMP<1 else 1,
                max_tokens=3000,
                # other params...
            )

            """This function invokes the action LLM and saves its completion to memory"""
            LLM_GENERATE_QUESTIONS_PROMPT_SELECTOR = get_questions_prompt_selector(lang="en", with_feedback=True if self.current_feedback else False)
            gen_questions_prompt = LLM_GENERATE_QUESTIONS_PROMPT_SELECTOR.get_prompt(self.action_model_id)

            ############----------Invoke model with prompt caching---------############

            if self.current_feedback:
                messages = gen_questions_prompt.format_messages(
                    industry=self.industry,
                    country=self.country,
                    workload=self.workload,
                    n_questions=n_questions,
                    regulation_portion=regulation_portion,
                    feedback=self.current_feedback,
                    output_format=QuestionGenerationOutput.model_json_schema()
                )
            else:
                messages = gen_questions_prompt.format_messages(
                    industry=self.industry,
                    country=self.country,
                    workload=self.workload,
                    n_questions=n_questions,
                    regulation_portion=regulation_portion,
                    output_format=QuestionGenerationOutput.model_json_schema()
                )

            # Create messages to invoke with prompt caching
            msgs = [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": messages[0].content,
                        },
                        {
                            "cachePoint": {"type": "default"}  # Need to create messages for prompt caching
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": messages[1].content
                        }
                    ]
                }
            ]

            response = action_llm.invoke(msgs)

            self.current_qa_str = response.content

        except ClientError as exc:
            if exc.response['Error']['Code'] == 'ThrottlingException':
                self.logger.error("Bedrock throttling. To try again")
                raise BedrockRetryableError(str(exc))
            elif exc.response['Error']['Code'] == 'ModelTimeoutException':
                self.logger.error("Bedrock ModelTimeoutException. To try again")
                raise BedrockRetryableError(str(exc))
            elif exc.response['Error']['Code'] == 'ModelErrorException':
                ACTION_MODEL_TEMP = ACTION_MODEL_TEMP + 0.1
                self.logger.error("Bedrock ModelErrorException. To try again")
                raise BedrockRetryableError(str(exc))
            else:
                raise
        except self.bedrock_runtime.exceptions.ThrottlingException as throttlingExc:
            self.logger.error("Bedrock ThrottlingException. To try again")
            raise BedrockRetryableError(str(throttlingExc))
        except self.bedrock_runtime.exceptions.ModelTimeoutException as timeoutExc:
            self.logger.error("Bedrock ModelTimeoutException. To try again")
            raise BedrockRetryableError(str(timeoutExc))
        except self.bedrock_runtime.exceptions.ModelErrorException as modelErrExc:
            ACTION_MODEL_TEMP = ACTION_MODEL_TEMP + 0.1
            self.logger.error("Bedrock ModelErrorException. To try again")
            raise BedrockRetryableError(str(modelErrExc))
        except Exception as e:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            self.logger.error(message)
            raise


    @retry(wait_exponential_multiplier=10000, wait_exponential_max=900000, stop_max_attempt_number=9,
           retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
    def evaluate(
        self,
    ):

        global EVAL_MODEL_TEMP
        qpoints = 0

        try:
            evaluator_llm = ChatBedrockConverse(
                model=self.evaluator_model_id,
                temperature=EVAL_MODEL_TEMP if EVAL_MODEL_TEMP < 1 else 1,
                max_tokens=8000,
                # other params...
            )

            """This function evaluates wether the task was succesful or not (binary evaluation)"""


            LLM_EVALUATE_QUESTIONS_PROMPT_SELECTOR = get_question_eval_prompt_selector(lang="en")
            gen_evals_prompt = LLM_EVALUATE_QUESTIONS_PROMPT_SELECTOR.get_prompt(self.evaluator_model_id)
            evaluate_questions_llm_chain = gen_evals_prompt | evaluator_llm

            qevals_text = evaluate_questions_llm_chain.invoke(
                {
                    "industry":self.industry,
                    "country":self.country,
                    "json_eval":QuestionEvaluation.model_json_schema(),
                    "workload":self.workload,
                    "gold_standard_questions":self.gold_standard_questions_str,
                    "questions":"\n".join(self.current_qa)
                }
            )

            return qevals_text

        except ClientError as exc:
            if exc.response['Error']['Code'] == 'ThrottlingException':
                self.logger.error("Bedrock throttling. To try again")
                raise BedrockRetryableError(str(exc))
            elif exc.response['Error']['Code'] == 'ModelTimeoutException':
                self.logger.error("Bedrock ModelTimeoutException. To try again")
                raise BedrockRetryableError(str(exc))
            elif exc.response['Error']['Code'] == 'ModelErrorException':
                EVAL_MODEL_TEMP = EVAL_MODEL_TEMP + 0.1
                self.logger.error("Bedrock ModelErrorException. To try again")
                raise BedrockRetryableError(str(exc))
            else:
                raise
        except self.bedrock_runtime.exceptions.ThrottlingException as throttlingExc:
            self.logger.error("Bedrock ThrottlingException. To try again")
            raise BedrockRetryableError(str(throttlingExc))
        except self.bedrock_runtime.exceptions.ModelTimeoutException as timeoutExc:
            self.logger.error("Bedrock ModelTimeoutException. To try again")
            raise BedrockRetryableError(str(timeoutExc))
        except self.bedrock_runtime.exceptions.ModelErrorException as modelErrExc:
            EVAL_MODEL_TEMP = EVAL_MODEL_TEMP + 0.1
            self.logger.error("Bedrock ModelErrorException. To try again")
            raise BedrockRetryableError(str(modelErrExc))
        except Exception as e:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            self.logger.error(message)
            raise


    @retry(wait_exponential_multiplier=10000, wait_exponential_max=900000, stop_max_attempt_number=9,
           retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
    def do_reflexion(
        self,
    ):

        global REFLEXION_MODEL_TEMP

        try:
            reflexion_llm = ChatBedrockConverse(
                model=self.reflexion_model_id,
                temperature=REFLEXION_MODEL_TEMP if REFLEXION_MODEL_TEMP < 1 else 1,
                max_tokens=3000,
                # other params...
            )

            """This function performs self-reflexion on the task completed by the actor"""

            LLM_REFLEXION_PROMPT_SELECTOR = get_reflexion_prompt_selector(lang="en")
            gen_reflexion_prompt = LLM_REFLEXION_PROMPT_SELECTOR.get_prompt(self.reflexion_model_id)
            reflexion_llm_chain = gen_reflexion_prompt | reflexion_llm

            reflexion = reflexion_llm_chain.invoke(
                {
                    "industry":self.industry,
                    "country":self.country,
                    "workload":self.workload,
                    "gold_standard_questions":self.gold_standard_questions_str,
                    "questions":"\n".join(self.current_qa),
                    "score": self.current_score
                }
            )

            return reflexion.content

        except ClientError as exc:
            if exc.response['Error']['Code'] == 'ThrottlingException':
                self.logger.error("Bedrock throttling. To try again")
                raise BedrockRetryableError(str(exc))
            elif exc.response['Error']['Code'] == 'ModelTimeoutException':
                self.logger.error("Bedrock ModelTimeoutException. To try again")
                raise BedrockRetryableError(str(exc))
            elif exc.response['Error']['Code'] == 'ModelErrorException':
                REFLEXION_MODEL_TEMP = REFLEXION_MODEL_TEMP + 0.1
                self.logger.error("Bedrock ModelErrorException. To try again")
                raise BedrockRetryableError(str(exc))
            else:
                raise
        except self.bedrock_runtime.exceptions.ThrottlingException as throttlingExc:
            self.logger.error("Bedrock ThrottlingException. To try again")
            raise BedrockRetryableError(str(throttlingExc))
        except self.bedrock_runtime.exceptions.ModelTimeoutException as timeoutExc:
            self.logger.error("Bedrock ModelTimeoutException. To try again")
            raise BedrockRetryableError(str(timeoutExc))
        except self.bedrock_runtime.exceptions.ModelErrorException as modelErrExc:
            REFLEXION_MODEL_TEMP = REFLEXION_MODEL_TEMP + 0.1
            self.logger.error("Bedrock ModelErrorException. To try again")
            raise BedrockRetryableError(str(modelErrExc))
        except Exception as e:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            self.logger.error(message)
            raise


    def execute_task(
        self,
        n_questions:str,
        regulation_portion:str,
    ):

        global STRUCTURED_OUTPUT_MODEL_TEMP, ACTION_MODEL_TEMP, EVAL_MODEL_TEMP, REFLEXION_MODEL_TEMP

        STRUCTURED_OUTPUT_MODEL_TEMP = 0.2
        ACTION_MODEL_TEMP = 0.6
        EVAL_MODEL_TEMP = 0.6
        REFLEXION_MODEL_TEMP = 0.6

        qpoints = 0
        trial_number = 0

        print(f"\n\nRunning trial {trial_number+1}")

        """\n\nCreate set of questions"""
        print("Performing task\n\n")
        
        self.perform_task(
            n_questions=n_questions,
            regulation_portion=regulation_portion,
        )

        print("\n\nCurrent set of questions\n\n")
        print(self.current_qa_str)

        self.chunk_topic_related, self.current_qa = self.get_last_question_batch()
        print("\n\nCurrent set of questions\n\n")
        print(self.current_qa)

        if self.chunk_topic_related:

            # Evaluate set of questions
            print("\n\nEvaluating task\n\n")
            qevals_text = self.evaluate()

            qevals = self.get_evals(qevals_text)

            print("\n\nEvaluations\n\n")
            print(qevals)

            for eval in qevals.question_evals:
                qpoints = qpoints + (eval.is_simple + eval.is_standalone + eval.aligned_to_gold_standard)

            self.current_score = qpoints / (len(qevals.question_evals) * 3)

        """If the score is not achieved or we still have rounds to go, do reflexion"""
        while (self.current_score < self.expected_score) and (trial_number < self.max_trials) and self.chunk_topic_related:

            STRUCTURED_OUTPUT_MODEL_TEMP = 0.2
            ACTION_MODEL_TEMP = 0.6
            EVAL_MODEL_TEMP = 0.6
            REFLEXION_MODEL_TEMP = 0.6

            qpoints = 0

            trial_number = trial_number + 1

            print(f"\n\nRunning trial {trial_number+1}\n\n")

            print("\n\nDoing reflexion")
            self.current_feedback = self.do_reflexion(
            )
            print("\n\nModel reflexion\n\n")
            print(self.current_feedback)

            """Append results to memory"""
            self.memory.append(self.current_feedback)

            """
            self.memory.append(
                {
                    "questions": self.current_qa.questions,
                    "evaluations": qevals.evaluations,
                    "points": qpoints
                }
            )
            """

            """Create set of questions"""
            print("\n\nPerforming task\n\n")
            self.perform_task(
                n_questions=n_questions,
                regulation_portion=regulation_portion,
            )

            print("\n\nCurrent set of questions\n\n")
            print(self.current_qa_str)
    
            self.chunk_topic_related, self.current_qa = self.get_last_question_batch()
            print("\n\nCurrent set of questions\n\n")
            print(self.current_qa)

            if self.chunk_topic_related:
    
                """Evaluate set of questions"""
                print("\n\nEvaluating task\n\n")
                qevals_text = self.evaluate(
                )

                qevals = self.get_evals(qevals_text)
                print("\n\nEvaluations\n\n")
                print(qevals)

                for eval in qevals.question_evals:
                    qpoints = qpoints + (eval.is_simple + eval.is_standalone + eval.aligned_to_gold_standard)

                self.current_score = qpoints/(len(qevals.question_evals)*3)

        if self.current_score >= self.expected_score:
            print(f"\n\nTask completed with score {self.current_score}")
            self.stop_reason = StopReason.SCORE_REACHED

        if trial_number >= self.max_trials:
            print(f"\n\nTask completed with MAX trials and a SCORE: {self.current_score}")
            self.stop_reason = StopReason.MAX_TRIALS

        if not self.chunk_topic_related:
            print(f"\n\nTask not completed because the chunk is not topic related")
            self.stop_reason = StopReason.CHUNK_NOT_RELEVANT