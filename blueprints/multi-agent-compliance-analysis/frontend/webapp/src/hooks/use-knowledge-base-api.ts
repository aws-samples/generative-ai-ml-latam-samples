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
import { getKnowledgeBasePresignedUrlApiUrl, getKnowledgeBaseProcessDocumentApiUrl } from "@/lib/api-endpoints"
import type { PresignedPostData } from "@/types"

export const useKnowledgeBaseApi = () => {
  const { makeAuthenticatedRequest, getAuthToken } = useAuthApi()

  const cleanFileName = (fileName: string): string => {
    return fileName
      .trim()
      .replace(/\s+/g, '') // Remove all whitespace
      .replace(/[^a-zA-Z0-9._-]/g, '') // Remove special characters except dots, hyphens, and underscores
  }

  const getPresignedUrl = async (fileName: string): Promise<PresignedPostData> => {
    try {
      const cleanedFileName = cleanFileName(fileName)
      const url = getKnowledgeBasePresignedUrlApiUrl(cleanedFileName)
      
      const token = await getAuthToken()
      
      const response = await fetch(url, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error("Error response body:", errorText)
        throw new Error(`Failed to get presigned URL: ${response.status} ${response.statusText} - ${errorText}`)
      }

      const data = await response.json()
      console.log("Presigned URL response (parsed JSON):", JSON.stringify(data, null, 2))
      return data
    } catch (error) {
      console.error("Error getting presigned URL:", error)
      throw error
    }
  }

  const uploadToS3 = async (file: File, presignedData: PresignedPostData) => {
    try {
      const { url, fields } = presignedData.presigned_post
      const formData = new FormData()
      
      Object.keys(fields).forEach(key => {
        formData.append(key, fields[key])
      })
      
      formData.append('file', file)
      
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error("S3 upload error response:", errorText)
        throw new Error(`S3 upload failed: ${response.status} ${response.statusText} - ${errorText}`)
      }

      console.log("File uploaded successfully to S3")
      return response
    } catch (error) {
      console.error("Error uploading to S3:", error)
      throw error
    }
  }

  const processDocument = async (s3Key: string, metadata: { filename: string; doc_key: string }) => {
    try {
      const url = getKnowledgeBaseProcessDocumentApiUrl()
      
      const data = await makeAuthenticatedRequest(url, {
        method: "POST",
        body: JSON.stringify({
          key: s3Key,
          metadata
        })
      })

      console.log("Document processed successfully:", data)
      return data
    } catch (error) {
      console.error("Error processing document:", error)
      throw error
    }
  }

  return {
    getPresignedUrl,
    uploadToS3,
    processDocument,
    cleanFileName,
  }
}
