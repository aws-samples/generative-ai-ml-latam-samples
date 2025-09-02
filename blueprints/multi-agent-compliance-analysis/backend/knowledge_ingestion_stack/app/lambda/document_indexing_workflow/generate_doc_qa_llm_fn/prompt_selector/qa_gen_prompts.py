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

NOVA_QA_SYSTEM_PROMPT_EN = """
You are {role} expert presented with a list, found in <qa_set> of question and answers obtained from several chunks of a large document. Your task is to derive a unique set of questions and answers that is representative of the entire document from a {perspective} perspective.

You can execute your task in any of your supported languages so start by determining the language of the QA set and place it in <task_language>

To get a unique set of questions and answers consider:

- Deduplication of the questions: remove duplicated or paraphrased questions
- Relevance of questions: keep questions that seem more relevant to a {role} under a {perspective} perspective
- Q&A set breath: keep a set of questions and answers that cover a vast range of topics under the {perspective} perspective
- Never leave unanswered questions. Every question must have an answer and viceversa
- Do not come up with new questions of your own. Just process the given set of questions and answers
- There is no limit on the number of questions and answer pairs you can keep

To de-duplicate the question set use the following reasoning for each question:

1. Identify the subject, topic, and intent of each question
2. Immediately remove any question with ambiguous or unspecified subject or topic
3. Compare against the other questions based on subject, topic, and intent
4. If subject, topic, and intent are repeated discard one pair of questions and answers. Keep the question and answer pair that provides more information

Let me show you some examples:

<qa_set>

<qa_pair>
Question: How does the institution ensure that contracted service providers have business continuity and disaster recovery plans?

Answer: The institution must ensure that contracted service providers have business continuity and disaster recovery plans that not only cover the restoration of their services but also the recovery of the institution's data, and that allow the institution to formally test these plans on a regular basis.
</qa_pair>

<qa_pair>
Question: What measures does the institution take to ensure that its external providers have adequate business continuity and disaster recovery plans?

Answer: The institution verifies that its external service providers implement business continuity and disaster recovery plans that guarantee both the restoration of services and the recovery of institutional data, in addition to establishing protocols to regularly test the effectiveness of these plans.
</qa_pair>

</qa_set>


Reason about your set of questions and decide if it complies with the considerations outlined before. Write down your reasoning in <reasoning> tag.

Write down your final set of Q&A within <qa_final_set>. DO NOT alter the questions or answers. Just decide if you wanna keep a pair

Always execute your task in the language specified in <task_language>

"""

NOVA_QA_USER_PROMPT_EN = """Generate a unique set of questions and answers given the following list of Q&A for each chunk of the document. 

<qa_set>
{qa_by_chunks}
</qa_set>
"""

NOVA_STRUCTURED_QA_GENERATION_EN = """
Extract, verbatim, the set of questions and answers from the given text:

{qa_text}

Extract only the question and answer without preambles, numbers or labels. For instance remove "Question:" and "Answer:" labels
"""