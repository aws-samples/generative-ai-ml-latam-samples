// MIT No Attribution
//
// Copyright 2025 Amazon Web Services
//
// Permission is hereby granted, free of charge, to any person obtaining a copy of this
// software and associated documentation files (the "Software"), to deal in the Software
// without restriction, including without limitation the rights to use, copy, modify,
// merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
// permit persons to whom the Software is furnished to do so.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
// INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
// PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
// HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
// OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
// SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

// File-related type definitions

export interface FileData {
  document_name: string
  document_key: string
  document_filekey: string
  main_job_id: string
  job_id: string
  status: string
}

export interface OptimisticFileData {
  id: string
  name: string
  fileName: string
  metadata: {
    filename: string
    doc_key: string
  }
}

export interface IngestedDocument {
  document_name: string
  document_key: string
  document_filekey: string
  job_id: string
  status: "DATA_INDEXING" | "QA_GENERATION" | "SUCCESS" | "ERROR"
  timestamp: number
}

export interface PresignedPostData {
  presigned_post: {
    url: string
    fields: {
      key: string
      "x-amz-algorithm": string
      "x-amz-credential": string
      "x-amz-date": string
      "x-amz-security-token": string
      policy: string
      "x-amz-signature": string
      [key: string]: string
    }
  }
}
