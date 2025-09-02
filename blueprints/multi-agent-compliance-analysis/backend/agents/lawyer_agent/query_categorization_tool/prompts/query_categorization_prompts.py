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

QUERY_CATEGORIZATION_SYSTEM_PROMPT_EN = """
You are given a query made by the user and a list of roles and their perspectives (as a python dictionary). Your task is to decide, 
which combinations of role and their allowed perspectives are better for answering the user's query, a role and perspective combination is called a query category. 

Follow these rules to assign a category to the query:

* Always categorize the query. Do not leave queries without category
* Do not make up roles of your own. Use only the valid roles
* Each role is specialized in a set of perspectives, only pick from the perspectives that the selected role can answer
* Attempt to categorize a question multiple times to allow for diversity but recommend more than one category only if its valuable

Follow this steps to categorize a query:

1. Decide which role is well suited to answer the query
2. From the list of available perspectives for the role select a perspective which could be of relevance for answering the query
3. Iterate until you have generated the requested set of categorizations

This is the list of allowed roles and categories:

{roles_categories}
"""

QUERY_CATEGORIZATION_USER_PROMPT_EN = """
Categorize the following query, provide at most {n_categories} categories

User query: {query}
"""