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

class ComplianceReportStatusEnum(Enum):
    AWAITING = 1
    CHUNKING = 2
    STRUCTURING = 3
    READY = 4
    QUESTION_ANSWERING = 5
    REPORT_GENERATION = 6
    SUCCESS = 7
    ERROR = -1

class QuestionStatusEnum(Enum):
    TEXT_EXTRACTION = 1
    PAGE_CHUNKING = 2
    PERSPECTIVE_MAPPING = 3
    CHUNK_QUESTION_GENERATION = 4
    DOCUMENT_QUESTION_CONSOLIDATION = 5
    GLOBAL_QUESTION_CONSOLIDATION = 6
    QUESTION_PERSISTENCE = 7
    SUCCESS = 8
    ERROR = -1

class IndexingStatusEnum(Enum):
    TEXT_EXTRACTION = 1
    PAGE_CHUNKING = 2
    METADATA_EXTRACTION = 3
    QA_GENERATION = 4
    METADATA_CONSOLIDATION = 5
    QA_CONSOLIDATION = 6
    SUMMARY_GENERATION = 7
    DATA_INDEXING = 8
    SUCCESS = 9
    ERROR = -1