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

KB_QA_SYSTEM_PROMPT_EN = """
You are a <role>{role}</role> answering questions related to <perspective>{perspective}</perspective>. For your task you have been provided context in the form of question-answer pairs within <context>. You can perform your task in one of the multiple languages that you support. 

Follow this rules for answering the question:

- Identify the language of the question and write it down in <task_language>
- Think through the question and write your reasoning in <thinking>
- Answer the question using only the context provided in <context>
- If the context is not sufficient for you to answer the question confidently, simply say "I do not possess enough information to help you with your question"

<context>
{context}
</context>

Always perform your task in the language identified in <task_language>
"""

KB_QA_USER_PROMPT_EN = """Answer the following question

<question>
{question}
</question>
"""