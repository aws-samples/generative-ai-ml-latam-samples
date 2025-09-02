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

import { useState } from "react"
import type { TemplateWithQuestions } from "@/types"
import { useAuthApi } from "./use-auth-api"
import { getJobQuestionsApiUrl } from "@/lib/api-endpoints"

export const useQuestionsData = () => {
  const [questionsData, setQuestionsData] = useState<Record<string, TemplateWithQuestions>>({})
  const [loadingQuestions, setLoadingQuestions] = useState<Record<string, boolean>>({})
  const { makeAuthenticatedRequest } = useAuthApi()

  const fetchQuestions = async (jobId: string): Promise<void> => {
    try {
      setLoadingQuestions(prev => ({ ...prev, [jobId]: true }))
      
      const apiUrl = getJobQuestionsApiUrl(jobId)
      const responseData = await makeAuthenticatedRequest(apiUrl)

      // Parse the template_with_questions JSON string
      if (responseData.template_with_questions) {
        const parsedQuestions: TemplateWithQuestions = responseData.template_with_questions
        setQuestionsData(prev => ({ ...prev, [jobId]: parsedQuestions }))
      }

    } catch (error) {
      console.error('Error fetching questions:', error)
    } finally {
      setLoadingQuestions(prev => ({ ...prev, [jobId]: false }))
    }
  }

  // Function to handle optimistic updates to questions
  const handleUpdateQuestions = (jobId: string, updatedQuestions: TemplateWithQuestions) => {
    setQuestionsData(prev => ({ ...prev, [jobId]: updatedQuestions }))
  }

  const clearQuestionsData = () => {
    setQuestionsData({})
    setLoadingQuestions({})
  }

  return {
    questionsData,
    loadingQuestions,
    fetchQuestions,
    handleUpdateQuestions,
    clearQuestionsData,
  }
}
