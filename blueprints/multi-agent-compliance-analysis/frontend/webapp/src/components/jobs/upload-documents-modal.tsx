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

import type React from "react"
import { useState, useRef } from "react"
import { useTranslation } from "react-i18next"
import { fetchAuthSession } from "aws-amplify/auth"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Upload, X, FileText, Trash2, AlertCircle, CheckCircle, Clock } from "lucide-react"
import type { UploadedFile, PresignedPostData, UploadDocumentsModalProps } from "@/types"

export function UploadDocumentsModal({ 
  open, 
  onClose, 
  onUploadComplete, 
  onOptimisticFileAdd,
  onFileStatusUpdate,
  onOptimisticFileRemove,
  jobId 
}: UploadDocumentsModalProps) {
  const { t } = useTranslation()
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i]
  }

  const generateFileId = () => `f${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

  const cleanFileName = (fileName: string): string => {
    // Maximum characters reduced to 45 for stricter filename limits
    const maxLength = 45
    
    // Remove whitespace and special characters, keep only alphanumeric, dots, hyphens, and underscores
    let cleanedName = fileName
      .trim()
      .replace(/\s+/g, '') // Remove all whitespace
      .replace(/[^a-zA-Z0-9._-]/g, '') // Remove special characters except dots, hyphens, and underscores
    
    // If the cleaned name exceeds the maximum length, slice it
    if (cleanedName.length > maxLength) {
      // Try to preserve the file extension if possible
      const lastDotIndex = cleanedName.lastIndexOf('.')
      if (lastDotIndex > 0 && lastDotIndex < cleanedName.length - 1) {
        const extension = cleanedName.substring(lastDotIndex)
        const nameWithoutExtension = cleanedName.substring(0, lastDotIndex)
        const maxNameLength = maxLength - extension.length
        
        if (maxNameLength > 0) {
          cleanedName = nameWithoutExtension.substring(0, maxNameLength) + extension
        } else {
          // If extension is too long, just slice the whole name
          cleanedName = cleanedName.substring(0, maxLength)
        }
      } else {
        // No extension or invalid extension, just slice
        cleanedName = cleanedName.substring(0, maxLength)
      }
    }
    
    return cleanedName
  }

  const getPresignedUrl = async (fileName: string): Promise<PresignedPostData> => {
    try {
      const session = await fetchAuthSession()
      const token = session.tokens?.idToken?.toString()

      if (!token) {
        throw new Error("No authentication token available")
      }

      const cleanedFileName = cleanFileName(fileName)
      
      const response = await fetch(
        `${import.meta.env.VITE_API_GATEWAY_REST_API_ENDPOINT_QUESTION_GENRATOR}/compliance-report/question-generator/upload/banking-core/${cleanedFileName}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      )

      if (!response.ok) {
        const errorText = await response.text()
        console.error("Error response body:", errorText)
        throw new Error(`Failed to get presigned URL: ${response.status} ${response.statusText} - ${errorText}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error("Error getting presigned URL:", error)
      throw error
    }
  }

  const uploadToS3 = async (file: File, presignedData: PresignedPostData) => {
    try {
      const { url, fields } = presignedData.presigned_post;
      const formData = new FormData();
      
      Object.keys(fields).forEach(key => {
        formData.append(key, fields[key]);
      });
      
      formData.append('file', file);

      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("S3 upload error response:", errorText);
        throw new Error(`S3 upload failed: ${response.status} ${response.statusText} - ${errorText}`);
      }
      
      // Extract the key from the presigned data and save to localStorage
      const s3Key = presignedData.presigned_post.fields.key;
      localStorage.setItem('lastUploadedS3Key', s3Key);
      
      return response;

    } catch (error) {
      console.error("Error uploading to S3:", error)
      throw error
    }
  }

  const processDocument = async (s3Key: string, metadata: { filename: string; doc_key: string }) => {
    try {
      const session = await fetchAuthSession()
      const token = session.tokens?.idToken?.toString()

      if (!token) {
        throw new Error("No authentication token available")
      }

      if (!jobId) {
        throw new Error(`No job ID available for document processing. Please ensure a job is selected.`)
      }

      const response = await fetch(
        `${import.meta.env.VITE_API_GATEWAY_REST_API_ENDPOINT_QUESTION_GENRATOR}/compliance-report/question-generator/processDocument`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            key: s3Key,
            main_job_id: jobId,
            metadata
          })
        }
      )

      if (!response.ok) {
        const errorText = await response.text()
        console.error("Process document error response:", errorText)
        throw new Error(`Failed to process document: ${response.status} ${response.statusText} - ${errorText}`)
      }

      const result = await response.json()
      return result

    } catch (error) {
      console.error("Error processing document:", error)
      throw error
    }
  }

  const uploadFile = async (fileId: string) => {
    const fileToUpload = files.find(f => f.id === fileId)
    if (!fileToUpload || !jobId) return

    const tempJobId = `optimistic_${fileId}`

    try {
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, status: "uploading" as const, progress: 10 } : f
      ))

      // Update optimistic file status to uploading
      onFileStatusUpdate(tempJobId, {
        document_name: fileToUpload.metadata.filename,
        document_key: fileToUpload.metadata.doc_key,
        document_filekey: `banking-core/${fileToUpload.fileName}`,
        main_job_id: jobId,
        job_id: tempJobId,
        status: "UPLOADING"
      })

      const presignedData = await getPresignedUrl(fileToUpload.fileName)
      
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, progress: 50 } : f
      ))

      await uploadToS3(fileToUpload.file, presignedData)

      // Extract and store the S3 key
      const s3Key = presignedData.presigned_post.fields.key
      
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, status: "uploaded" as const, progress: 70, s3Key } : f
      ))

      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, status: "processing" as const, progress: 85 } : f
      ))

      // Update optimistic file status to processing
      onFileStatusUpdate(tempJobId, {
        document_name: fileToUpload.metadata.filename,
        document_key: fileToUpload.metadata.doc_key,
        document_filekey: s3Key,
        main_job_id: jobId,
        job_id: tempJobId,
        status: "DOCUMENT_PROCESSING"
      })

      const processResult = await processDocument(s3Key, fileToUpload.metadata)

      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, status: "completed" as const, progress: 100 } : f
      ))

      // Update optimistic file with final data from API response
      if (processResult && processResult.job_id) {
        onFileStatusUpdate(tempJobId, {
          document_name: fileToUpload.metadata.filename,
          document_key: fileToUpload.metadata.doc_key,
          document_filekey: s3Key,
          main_job_id: jobId,
          job_id: processResult.job_id, // Use real job_id from API
          status: "QUESTION_GENERATION" // Or whatever status the API returns
        })
      }

    } catch (error) {
      console.error("Upload failed:", error)
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, status: "error" as const } : f
      ))

      // Remove failed optimistic update
      onOptimisticFileRemove(tempJobId)
    }
  }

  const handleFileSelect = (selectedFiles: FileList | null) => {
    if (!selectedFiles) return

    const newFiles: UploadedFile[] = Array.from(selectedFiles).map((file) => {
      const cleanedFileName = cleanFileName(file.name)
      const cleanedDisplayName = cleanFileName(file.name.replace(/\.[^/.]+$/, "")) // Remove file extension and clean
      const cleanedDocKey = cleanFileName(file.name.toLowerCase().replace(/[^a-z0-9]/g, "_").replace(/_{2,}/g, "_").replace(/^_|_$/g, ""))
      
      return {
        id: generateFileId(),
        name: file.name,
        fileName: cleanedFileName,
        size: formatFileSize(file.size),
        status: "ready" as const,
        progress: 0,
        file,
        metadata: {
          filename: cleanedDisplayName,
          doc_key: cleanedDocKey
        }
      }
    })

    setFiles((prev) => [...prev, ...newFiles])
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    handleFileSelect(e.dataTransfer.files)
  }

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId))
  }

  const updateFileName = (fileId: string, newFileName: string) => {
    const cleanedFileName = cleanFileName(newFileName)
    setFiles(prev => prev.map(f => 
      f.id === fileId ? { ...f, fileName: cleanedFileName } : f
    ))
  }

  const updateMetadataFilename = (fileId: string, filename: string) => {
    const cleanedFilename = cleanFileName(filename)
    setFiles(prev => prev.map(f => 
      f.id === fileId ? { ...f, metadata: { ...f.metadata, filename: cleanedFilename } } : f
    ))
  }

  const updateMetadataDocKey = (fileId: string, doc_key: string) => {
    const cleanedDocKey = cleanFileName(doc_key)
    setFiles(prev => prev.map(f => 
      f.id === fileId ? { ...f, metadata: { ...f.metadata, doc_key: cleanedDocKey } } : f
    ))
  }

  const handleUploadComplete = async () => {
    if (files.length === 0 || !jobId) return

    setIsUploading(true)

    // Trigger optimistic update immediately
    const filesToUpload = files.filter(f => f.status !== "completed")
    if (filesToUpload.length > 0) {
      onOptimisticFileAdd(jobId, filesToUpload.map(file => ({
        id: file.id,
        name: file.name,
        fileName: file.fileName,
        metadata: file.metadata
      })))
    }

    try {
      for (const file of files) {
        if (file.status !== "completed") {
          await uploadFile(file.id)
        }
      }

      // Wait a moment for all uploads to complete
      await new Promise(resolve => setTimeout(resolve, 1000))

      const completedFiles = files.filter(f => f.status === "completed")
      onUploadComplete(completedFiles)

      setFiles([])
      setIsUploading(false)
      onClose()
    } catch (error) {
      console.error("Upload process failed:", error)
      
      // Remove failed optimistic updates
      const failedFiles = files.filter(f => f.status === "error")
      failedFiles.forEach(file => {
        onOptimisticFileRemove(`optimistic_${file.id}`)
      })
      
      setIsUploading(false)
    }
  }

  const canUpload = files.length > 0 && 
    files.every(f => 
      f.fileName.trim() !== "" && 
      f.metadata.filename.trim() !== "" && 
      f.metadata.doc_key.trim() !== ""
    )
  const hasUploadingFiles = files.some((f) => f.status === "uploading" || f.status === "processing")

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] mx-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="space-y-1">
            <h2 className="text-2xl font-bold text-gray-900">{t('documents.uploadDocuments')}</h2>
            <p className="text-sm text-gray-600">{t('documents.uploadDocumentsDescription')}</p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* File Upload Area */}
          <div className="space-y-4">
            <Label className="text-sm font-medium text-gray-700">{t('documents.documents')} *</Label>

            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                isDragOver ? "border-violet-400 bg-violet-50" : "border-gray-300 hover:border-gray-400"
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="space-y-4">
                <div className="p-3 bg-gray-100 rounded-full w-fit mx-auto">
                  <Upload className="w-6 h-6 text-gray-600" />
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium text-gray-900">
                    {t('documents.dropFiles')}{" "}
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="text-violet-600 hover:text-violet-700 font-semibold"
                    >
                      {t('documents.browse')}
                    </button>
                  </p>
                  <p className="text-xs text-gray-500">{t('documents.supportedFormats')}</p>
                </div>
              </div>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.doc,.docx"
              onChange={(e) => handleFileSelect(e.target.files)}
              className="hidden"
            />
          </div>

          {/* Files List */}
          {files.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium text-gray-700">{t('documents.uploadedFiles')}</Label>
                <Badge variant="secondary" className="text-xs">
                  {files.length} {files.length !== 1 ? t('documents.files') : t('documents.file')}
                </Badge>
              </div>

              <div className="space-y-3 max-h-60 overflow-y-auto">
                {files.map((file) => {
                  const getStatusIcon = () => {
                    switch (file.status) {
                      case "completed":
                        return <CheckCircle className="w-4 h-4 text-green-600" />
                      case "uploading":
                        return <Clock className="w-4 h-4 text-blue-600" />
                      case "uploaded":
                        return <CheckCircle className="w-4 h-4 text-blue-600" />
                      case "processing":
                        return <Clock className="w-4 h-4 text-purple-600" />
                      case "error":
                        return <AlertCircle className="w-4 h-4 text-red-600" />
                      case "ready":
                        return <Upload className="w-4 h-4 text-gray-600" />
                    }
                  }

                  const getStatusColor = () => {
                    switch (file.status) {
                      case "completed":
                        return "bg-green-50 border-green-200"
                      case "uploading":
                        return "bg-blue-50 border-blue-200"
                      case "uploaded":
                        return "bg-blue-50 border-blue-200"
                      case "processing":
                        return "bg-purple-50 border-purple-200"
                      case "error":
                        return "bg-red-50 border-red-200"
                      case "ready":
                        return "bg-gray-50 border-gray-200"
                      default:
                        return "bg-gray-50 border-gray-200"
                    }
                  }

                  return (
                    <div key={file.id} className={`p-4 rounded-lg border ${getStatusColor()}`}>
                      <div className="space-y-3">
                        {/* File info and status */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3 flex-1 min-w-0">
                            <div className="p-1.5 bg-white rounded">
                              <FileText className="w-4 h-4 text-gray-600" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                              <div className="flex items-center gap-3 mt-1">
                                <span className="text-xs text-gray-500">{file.size}</span>
                                {(file.status === "uploading" || file.status === "processing") && (
                                  <div className="flex items-center gap-2 flex-1">
                                    <Progress value={file.progress} className="h-1.5 flex-1 max-w-20" />
                                    <span className="text-xs text-gray-600 font-medium min-w-[3rem]">
                                      {file.progress}%
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {getStatusIcon()}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeFile(file.id)}
                              className="text-gray-400 hover:text-red-600 p-1"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          </div>
                        </div>

                        {/* File name input */}
                        <div className="space-y-2">
                          <Label className="text-xs font-medium text-gray-600">{t('documents.fileNameForS3')}</Label>
                          <Input
                            value={file.fileName}
                            onChange={(e) => updateFileName(file.id, e.target.value)}
                            placeholder={t('documents.fileNamePlaceholder')}
                            className="text-sm"
                            disabled={file.status === "uploading" || file.status === "uploaded" || file.status === "processing" || file.status === "completed"}
                          />
                          <div className="text-xs text-gray-500">
                            {file.fileName.length}/45 characters
                            {file.fileName.length >= 45 && (
                              <span className="text-amber-600 ml-1">(max reached)</span>
                            )}
                          </div>
                        </div>

                        {/* Metadata fields */}
                        <div className="grid grid-cols-2 gap-3">
                          <div className="space-y-2">
                            <Label className="text-xs font-medium text-gray-600">{t('documents.displayName')} *</Label>
                            <Input
                              value={file.metadata.filename}
                              onChange={(e) => updateMetadataFilename(file.id, e.target.value)}
                              placeholder={t('documents.displayNamePlaceholder')}
                              className="text-sm"
                              disabled={file.status === "uploading" || file.status === "uploaded" || file.status === "processing" || file.status === "completed"}
                            />
                            <div className="text-xs text-gray-500">
                              {file.metadata.filename.length}/45 characters
                              {file.metadata.filename.length >= 45 && (
                                <span className="text-amber-600 ml-1">(max reached)</span>
                              )}
                            </div>
                          </div>
                          <div className="space-y-2">
                            <Label className="text-xs font-medium text-gray-600">{t('documents.documentKey')} *</Label>
                            <Input
                              value={file.metadata.doc_key}
                              onChange={(e) => updateMetadataDocKey(file.id, e.target.value)}
                              placeholder={t('documents.documentKeyPlaceholder')}
                              className="text-sm"
                              disabled={file.status === "uploading" || file.status === "uploaded" || file.status === "processing" || file.status === "completed"}
                            />
                            <div className="text-xs text-gray-500">
                              {file.metadata.doc_key.length}/45 characters
                              {file.metadata.doc_key.length >= 45 && (
                                <span className="text-amber-600 ml-1">(max reached)</span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t bg-gray-50">
          <div className="text-sm text-gray-600">
            {files.length > 0 && (
              <span>
                {t('documents.filesProcessed', { 
                  completed: files.filter((f) => f.status === "completed").length, 
                  total: files.length 
                })}
              </span>
            )}
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={onClose} disabled={isUploading}>
              {t('common.cancel')}
            </Button>
            <Button
              onClick={handleUploadComplete}
              disabled={!canUpload || isUploading || hasUploadingFiles}
              className="bg-gradient-to-r from-[#742ed1] via-[#6f37d4] to-[#4d7ceb] hover:from-[#6a29c4] hover:via-[#6530c7] hover:to-[#4570de]"
            >
              {isUploading ? (
                <>
                  <Clock className="w-4 h-4 mr-2 animate-spin" />
                  {t('documents.processing')}
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  {t('documents.uploadAndProcess')}
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}