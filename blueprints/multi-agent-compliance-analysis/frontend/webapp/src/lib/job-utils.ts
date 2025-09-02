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

import type { Job, InternalJob, FileData, TemplateWithQuestions } from "@/types"

export const transformApiJobToInternalJob = (apiJob: Job): InternalJob => {
  let jobName = apiJob.analysis_name?.trim()
  if (!jobName) {
    jobName = `${apiJob.industry} - ${apiJob.workload} (${apiJob.country})`
  }
  
  const mapApiStatus = (apiStatus: string): string => {
    const upperStatus = apiStatus.toUpperCase()
    
    switch (upperStatus) {
      case 'SUCCESS':
        return 'completed'
      case 'READY':
        return 'ready_for_analysis'
      case 'AWAITING':
        return 'awaiting'
      case 'STRUCTURING':
        return 'processing'
      case 'QUESTION_ANSWERING':
      case 'REPORT_GENERATION':
        return 'question_answering'
      default:
        return apiStatus.toLowerCase()
    }
  }
  
  return {
    id: apiJob.job_id,
    name: jobName,
    workload: apiJob.workload,
    country: apiJob.country,
    industry: apiJob.industry,
    status: mapApiStatus(apiJob.status),
    createdAt: new Date().toISOString().split("T")[0], // Default to today since API doesn't provide this
    timestamp: apiJob.timestamp,
    files: [],
    questionsExtracted: 0,
    reportAvailable: false,
    extractedQuestions: [],
  }
}

export const sortJobsByTimestamp = (jobs: InternalJob[]): InternalJob[] => {
  return jobs.sort((a: InternalJob, b: InternalJob) => {
    if (a.timestamp && b.timestamp) {
      return b.timestamp - a.timestamp
    }
    if (a.timestamp && !b.timestamp) {
      return -1
    }
    if (!a.timestamp && b.timestamp) {
      return 1
    }
    return 0
  })
}

export const getFileCountForJob = (jobId: string, filesData: FileData[]): number => {
  return filesData.filter(file => file.main_job_id === jobId).length
}

export const getFilesForJob = (jobId: string, filesData: FileData[]): FileData[] => {
  return filesData.filter(file => file.main_job_id === jobId)
}

export const hasSuccessfulFiles = (jobId: string, filesData: FileData[]): boolean => {
  const files = getFilesForJob(jobId, filesData)
  return files.some(file => {
    const status = file.status.toLowerCase()
    return status === 'success' || status === 'completed'
  })
}

export const getTotalQuestionsCount = (questionsData: TemplateWithQuestions | undefined): number => {
  if (!questionsData) return 0
  
  return Object.values(questionsData).reduce((total, section) => {
    if (section.questions && Array.isArray(section.questions)) {
      return total + section.questions.length
    }
    return total
  }, 0)
}

export const isQuestionsLocked = (status: string): boolean => {
  const analyzingStatuses = [
    "analyzing", 
    "question_answering", 
    "processing",
    "structuring"
  ]
  return analyzingStatuses.includes(status.toLowerCase())
}

export const filterJobs = (
  jobs: InternalJob[], 
  searchTerm: string, 
  statusFilter: string
): InternalJob[] => {
  return jobs.filter((job) => {
    const matchesSearch =
      job.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.id.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === "all" || job.status === statusFilter
    return matchesSearch && matchesStatus
  })
}
