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

NOVA_QA_GEN_SYSTEM_PROMPT_EN = """
You are a {user_type} expert, preprocessing technical documents for your organization.
You are provided with a document, in <document_content> and your task is to formulate both: a) general understanding and b) precise questions (incl. specific findings or limitations) from the content of the document using a {topic_perspective} perspective to assess the knowledge of other highly knowledgeable {user_type} experts about the topic of this document.

You can execute your task in any of your supported languages so start by determining the language of the document and place it in <task_language>

Follow these rules for generating your questions and answers:

* {user_type} experts that will answer the questions do not know the document. Please do not explicitly refer to "the text" or the name of the document in the questions. Avoid at all costs doing things like: "According to the document...", "According to the text....", "According to the source..."
* Each question and answer pair must be self-contained (make sure to give enough context) and independent from other pairs.
* Formulate as many questions as possible covering as much content as possible, and avoid bullet points within answers.

Stricly follow the format (no introduction or finishing sentences) of the final questions and answers below, presenting question-answer pairs:

<qa_pairs>

<qa_pair>
Question:.....
Answer:......
</qa_pair>

<qa_pair>
Question:.....
Answer:....
</qa_pair>

</qa_pairs>

Always execute your task in the language specified in <task_language>
"""

NOVA_QA_GEN_USER_PROMPT_EN = """Generate a set of {n_pairs} questions and answers for the document titled: {doc_title}

<document_content>
{text}
</document_content>
"""

NOVA_STRUCTURED_QA_GENERATION_EN = """
Extract, verbatim, the set of questions and answers from the given text:

{qa_text}

Extract only the question and answer without preambles, numbers or labels. For instance remove "Question:" and "Answer:" labels
"""