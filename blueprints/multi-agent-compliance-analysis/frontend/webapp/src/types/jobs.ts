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

// Job-related type definitions

export interface Job {
  job_id: string
  country: string
  industry: string
  workload: string
  analysis_name: string
  status: string
  timestamp?: number
  template_with_questions?: string
}

export interface InternalJob {
  id: string
  name: string
  workload: string
  country: string
  industry: string
  status: string
  createdAt: string
  timestamp?: number
  files: LegacyUploadedFile[]
  questionsExtracted: number
  reportAvailable: boolean
  extractedQuestions: string[]
}

export interface JobCreationData {
  jobId: string
  analysisName: string
  workload: string
  country: string
  industry: string
  referenceQuestions: string[]
}

// Legacy UploadedFile interface for backward compatibility
export interface LegacyUploadedFile {
  id: string
  name: string
  size: string
  status: string
  progress: number
}
