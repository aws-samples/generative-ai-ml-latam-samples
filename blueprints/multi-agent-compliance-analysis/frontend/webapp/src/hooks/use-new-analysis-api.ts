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

import { useAuthApi } from "./use-auth-api"
import { getCreateAnalysisJobApiUrl } from "@/lib/api-endpoints"

export interface CreateAnalysisJobPayload {
  analysis_name: string
  workload: string
  country: string
  industry: string
  reference_questions: string[]
}

export interface CreateAnalysisJobResponse {
  job_id?: string
  jobId?: string
  id?: string
  [key: string]: any
}

export const useNewAnalysisApi = () => {
  const { makeAuthenticatedRequest } = useAuthApi()

  const createAnalysisJob = async (payload: CreateAnalysisJobPayload): Promise<CreateAnalysisJobResponse> => {
    try {
      const url = getCreateAnalysisJobApiUrl()
      
      const result = await makeAuthenticatedRequest(url, {
        method: 'POST',
        body: JSON.stringify(payload)
      })

      return result
    } catch (error) {
      console.error('Error creating analysis job:', error)
      throw error
    }
  }

  return {
    createAnalysisJob,
  }
}
