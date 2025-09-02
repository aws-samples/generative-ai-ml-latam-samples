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

export const getJobsApiUrl = (): string => {
  const baseUrl = import.meta.env.VITE_API_GATEWAY_REST_API_ENDPOINT_JOBS
  return `${baseUrl}/compliance-report/jobs/query`
}

export const getFilesApiUrl = (): string => {
  const baseUrl = import.meta.env.VITE_API_GATEWAY_REST_API_ENDPOINT_QUESTION_GENRATOR
  return `${baseUrl}/compliance-report/question-generator/jobs/query`
}

export const getJobQuestionsApiUrl = (jobId: string): string => {
  const baseUrl = import.meta.env.VITE_API_GATEWAY_REST_API_ENDPOINT_JOBS
  return `${baseUrl}/compliance-report/jobs/query/${jobId}`
}

export const getReportLayoutApiUrl = (): string => {
  const baseUrl = import.meta.env.VITE_API_GATEWAY_REST_API_ENDPOINT_JOBS
  return `${baseUrl}/compliance-report/reportLayout`
}

export const getStoreQuestionsApiUrl = (): string => {
  const baseUrl = import.meta.env.VITE_API_GATEWAY_REST_API_ENDPOINT_JOBS
  return `${baseUrl}/compliance-report/storeQuestions`
}

export const getStartAnalysisApiUrl = (): string => {
  const baseUrl = import.meta.env.VITE_API_GATEWAY_REST_API_ENDPOINT_JOBS
  return `${baseUrl}/compliance-report/startAnalysis`
}

export const getIndexDocumentsApiUrl = (): string => {
  const baseUrl = import.meta.env.VITE_API_GATEWAY_REST_API_ENDPOINT_INDEX_DOCUMENTS
  return `${baseUrl}/compliance-report/data-indexing`
}

export const getDownloadReportApiUrl = (jobId: string): string => {
  const baseUrl = import.meta.env.VITE_API_GATEWAY_REST_API_ENDPOINT_JOBS
  return `${baseUrl}/compliance-report/report/${jobId}`
}

// Knowledge Base API endpoints
export const getKnowledgeBasePresignedUrlApiUrl = (fileName: string): string => {
  const baseUrl = import.meta.env.VITE_API_GATEWAY_REST_API_ENDPOINT_INDEX_DOCUMENTS
  return `${baseUrl}/compliance-report/data-indexing/upload/banking-core/${fileName}`
}

export const getKnowledgeBaseProcessDocumentApiUrl = (): string => {
  const baseUrl = import.meta.env.VITE_API_GATEWAY_REST_API_ENDPOINT_INDEX_DOCUMENTS
  return `${baseUrl}/compliance-report/data-indexing/processDocument`
}

// New Analysis API endpoints
export const getCreateAnalysisJobApiUrl = (): string => {
  const baseUrl = import.meta.env.VITE_API_GATEWAY_REST_API_ENDPOINT_JOBS
  return `${baseUrl}/compliance-report/createAnalysisJob`
}
