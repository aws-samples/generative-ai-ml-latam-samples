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

# AMAZON NOVA PROMPT TEMPLATES

# English Prompts

NOVA_QUESTIONS_EVAL_SYSTEM_PROMPT_EN = """
You are a lawyer highly knowledgeable of the regulation regarding the {industry} industry in {country}. You have been hired by a company from the {industry} to assess if its {workload} processes are compliant with the regulation.

You have tasked one of your colleagues to generate a set of questions that will help you and your customer assess whether their <process>{workload} processes</process> complies or not with the law. Your task is to evaluate the set of questions your colleague has generated, found in <question_list>. You have at your disposal a set of "gold standard" set of curated questions in <gold_standard_questions> for you to compare against the questions your colleague generated.

You can execute your task in any of your supported languages so start by determining the language of the <gold_standard_questions> and place it in <task_language>. NEVER ASSUME the language of the task based on the country of the regulation.

Follow these rules for your task:

* Analyze each question separately
* The order of the questions is irrelevant
* You are evaluating the form of the questions rather than the content or context
* Compare the generated questions against the <gold_standard_questions> in terms of form and syntax. Do not compare them in terms of topic or content alignment

Evaluate each question in the set using the following framework presented as a JSON object:

<evaluation_framework>
{json_eval}
</evaluation_framework>

<gold_standard_questions>
{gold_standard_questions}
</gold_standard_questions>

Always execute your task in the language specified in <task_language>
"""


NOVA_QUESTIONS_EVAL_USER_PROMPT_EN = """Evaluate the following set of questions

<question_list>
{questions}
</question_list>

Answer only with the JSON object and nothing else. Do not add a preamble or anything after the JSON object

"""

NOVA_STRUCTURED_EVALUATIONS_GENERATION_EN = """
Extract, verbatim, the question evaluations in this text:

{question_evals}
"""