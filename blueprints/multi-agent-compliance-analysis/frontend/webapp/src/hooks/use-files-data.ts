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
import type { FileData, OptimisticFileData } from "@/types"
import { useAuthApi } from "./use-auth-api"
import { getFilesApiUrl } from "@/lib/api-endpoints"

export const useFilesData = () => {
  const [filesData, setFilesData] = useState<FileData[]>([])
  const [loadingFiles, setLoadingFiles] = useState(false)
  const { makeAuthenticatedRequest } = useAuthApi()

  const fetchFiles = async (): Promise<void> => {
    try {
      setLoadingFiles(true)
      
      const apiUrl = getFilesApiUrl()
      const data = await makeAuthenticatedRequest(apiUrl)
      setFilesData(data.items || [])
      
    } catch (err) {
      console.error('Error fetching files data:', err)
      // Don't set error state for files as it's not critical
    } finally {
      setLoadingFiles(false)
    }
  }

  // Optimistic update function for when files start uploading
  const handleOptimisticFileAdd = (jobId: string, files: OptimisticFileData[]): void => {
    // Create optimistic file entries that match the FileData interface
    const optimisticFiles: FileData[] = files.map(file => ({
      document_name: file.metadata.filename,
      document_key: file.metadata.doc_key,
      document_filekey: `banking-core/${file.fileName}`,
      main_job_id: jobId,
      job_id: `optimistic_${file.id}`, // Temporary ID for optimistic update
      status: "UPLOADING" // Custom status for optimistic updates
    }))

    // Add optimistic files to the filesData state
    setFilesData(prev => [...prev, ...optimisticFiles])
  }

  // Function to update file status after upload completion
  const handleFileStatusUpdate = (tempJobId: string, newFileData: FileData): void => {
    setFilesData(prev => 
      prev.map(file => 
        file.job_id === tempJobId ? newFileData : file
      )
    )
  }

  // Function to remove failed optimistic updates
  const handleOptimisticFileRemove = (tempJobId: string): void => {
    setFilesData(prev => 
      prev.filter(file => file.job_id !== tempJobId)
    )
  }

  // Cleanup function to remove stale optimistic updates
  const cleanupOptimisticUpdates = (): void => {
    setFilesData(prev => 
      prev.filter(file => !file.job_id.startsWith('optimistic_'))
    )
  }

  return {
    filesData,
    loadingFiles,
    fetchFiles,
    handleOptimisticFileAdd,
    handleFileStatusUpdate,
    handleOptimisticFileRemove,
    cleanupOptimisticUpdates,
  }
}
