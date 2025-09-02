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

import { useState, useEffect } from "react"
import type { InternalJob, JobCreationData } from "@/types"
import { useAuthApi } from "./use-auth-api"
import { getJobsApiUrl } from "@/lib/api-endpoints"
import { transformApiJobToInternalJob, sortJobsByTimestamp } from "@/lib/job-utils"

export const useJobsData = () => {
  const [jobs, setJobs] = useState<InternalJob[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { makeAuthenticatedRequest } = useAuthApi()

  const fetchJobs = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const apiUrl = getJobsApiUrl()
      const data = await makeAuthenticatedRequest(apiUrl)
      
      const transformedJobs = data.items.map(transformApiJobToInternalJob)
      const sortedJobs = sortJobsByTimestamp(transformedJobs)
      
      setJobs(sortedJobs)
    } catch (err) {
      console.error('Error fetching jobs:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch jobs')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateJob = (jobData: JobCreationData): void => {
    const newJob: InternalJob = {
      id: jobData.jobId,
      name: jobData.analysisName,
      workload: jobData.workload,
      country: jobData.country,
      industry: jobData.industry,
      status: "awaiting",
      createdAt: new Date().toISOString().split("T")[0],
      files: [],
      questionsExtracted: jobData.referenceQuestions.length,
      reportAvailable: false,
      extractedQuestions: jobData.referenceQuestions,
    }

    setJobs((prev) => [newJob, ...prev])
  }

  const updateJobStatus = (jobId: string, status: string) => {
    setJobs(prevJobs => 
      prevJobs.map(job => 
        job.id === jobId 
          ? { ...job, status }
          : job
      )
    )
  }

  useEffect(() => {
    fetchJobs()
  }, [])

  return {
    jobs,
    loading,
    error,
    fetchJobs,
    handleCreateJob,
    updateJobStatus,
  }
}
