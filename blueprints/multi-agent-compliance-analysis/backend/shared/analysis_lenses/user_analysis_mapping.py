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

from enum import Enum

# Set of perspectives that can be used to answer the auditor's queries
class AnalysisPerspectives(Enum):
    SECURITY = "software security engineer"
    DATA_GOVERNANCE = "data governance"
    RESILIENCY = "systems resiliency"
    SYS_OPS = "systems operations"

# Persona definition for answering the auditor's queries
AnalysisPersonas = {
    "software security engineer": {
        "description": "It is responsible for ensuring that workloads have the necessary security controls in place",
        "perspectives": [AnalysisPerspectives.SECURITY.value, AnalysisPerspectives.DATA_GOVERNANCE.value]
    },
    "solutions architect": {
        "description": "It is responsible for designing scalable and cost-efficient software solutions",
        "perspectives": [AnalysisPerspectives.RESILIENCY.value, AnalysisPerspectives.DATA_GOVERNANCE.value, AnalysisPerspectives.SECURITY.value]
    },
    "software developer": {
        "description":"Implements the system functionalities",
        "perspectives": [AnalysisPerspectives.SYS_OPS.value, AnalysisPerspectives.RESILIENCY.value, AnalysisPerspectives.SECURITY.value]
    }
}