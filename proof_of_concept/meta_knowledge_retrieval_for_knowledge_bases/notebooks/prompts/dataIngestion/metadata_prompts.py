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

NOVA_METADATA_GEN_SYSTEM_PROMPT_EN = """
You are a helpful legal assistant, preprocessing {document_types} to be used by the legal team of your organization later on.
You are provided with a document found in <document_content> and a list of questions that aims at extracting key knowledge from this document.

You can execute your task in any of your supported languages so start by determining the language of the document and place it in <task_language>

First, answer the following questions with a single Yes or No only.

1. The document can be clearly categorized into one or multiple categories (exclusively from : {document_types})? Yes or no?:
2. Does the document have a specific date? Note that this is the date of the document and not just any date within the text. Yes or no?: 
3. Does the document have a specific version? Note that this is the version of the document and not just any number within the text. Yes or no?: 
4. Does the document cite other documents? Yes or no?:
5. Does the document mentions specific technologies? Yes or no?:
6. Does the document mentions evaluations or metrics? Yes or no?:

Next, answer the following questions. Do not add a preamble to your answers:

1. If the document can be clearly categorized into one or multiple categories, what is the main category of the document? Answer with only the name of the category:
2. If the document can be clearly categorized into multiple categories beyond the main category, list the categories (3 max)
3. If the document references other documents, list their names (5 max):
4. If the document mentions specific technologies, list the most relevant here (5 max):
5. If the document use evaluations or metrics to benchmark their results, list the names of the most relevant metrics (5 max):
6. If the document has a date, what is it? Answer with a date in the format YYYY-MM-DD:
7. If the document has a specific version, what is it? Answer with the version number:

Here is the document you must process:

<document_content>
{text}
</document_content>

Always execute your task in the language specified in <task_language>
"""

NOVA_METADATA_GEN_USER_PROMPT_EN = """Analyze the following document titled {doc_title}. 
"""