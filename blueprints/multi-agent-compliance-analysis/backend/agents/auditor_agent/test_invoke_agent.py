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
import json

agent_core_client = boto3.client('bedrock-agentcore', region_name='us-east-1')

payload = json.dumps({
    "input": {
      "industry": "Financial services",
      "country": "Mexico",
      "workload": "Banking core",
      "section": "Security",
      "description": "This section talks about the security of the workload",
      "markdown_report": "",
      "questions": [
        "¿Se anonimizan los datos?",
        "¿Cual es la funcion del CISO?"
      ]
    }
  })

response = agent_core_client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:592992680099:runtime/compliance_analysis_auditor_agent-Haxc25ExeO',
    runtimeSessionId='dfmeoagmreaklgmrkleafremoigrmtesogmtrskhmtkrlshmt',  # Must be 33+ chars
    payload=payload,
    qualifier="DEFAULT"
)

response_body = response['response'].read()
response_data = json.loads(response_body)
print("Agent Response:", response_data)