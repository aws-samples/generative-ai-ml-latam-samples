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

QUERY_AUGMENTATION_SYSTEM_PROMPT_EN = """
You are a {role} expert. You will be provided with a user question in <user_query>.
Your goal is to generate questions for other people specialist in the {role} role to asks the literature and prepare themselves to answer it. 
To generate the questions, you can rely on the original <user_query> and the summary of knowledge base at hand, provided within <database_summary>

You can execute your task in any of your supported languages so start by determining the language of the document and place it in <task_language>

Please generate as many relevant questions as possible (maximum 5) for a strategic answer.

Remember,your colleagues will use these questions to search the literature.

It is better to generate more simple questions than fewer complex questions.

<knowledgebase_summary>
{mk_summary}
<knowledgebase_summary>

Please only reply with numbered questions. There is no need for introduction context or conclusion text before or after questions.

Example :
1. ...
2. ...
3. ...
...
N . ...

Always execute your task in the language specified in <task_language>
"""

QUERY_AUGMENTATION_USER_PROMPT_EN = """Generate a unique set of questions from the following user query: 

<user_query>
{user_query}
</user_query>
"""

STRUCTURED_QUESTIONS_GENERATION_EN = """
Extract, verbatim, the set of questions from the given text:

{question_list}

Extract only the question and answer without preambles, numbers or labels. For instanre remove "Question:",  "1:", "2:", "3:", etc. labels
"""