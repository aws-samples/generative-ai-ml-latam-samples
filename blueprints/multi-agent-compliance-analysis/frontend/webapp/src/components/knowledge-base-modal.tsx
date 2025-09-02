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
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Upload, X, FileText, Trash2, AlertCircle, CheckCircle, Clock } from "lucide-react"
import type { UploadedFile, KnowledgeBaseModalProps } from "@/types"
import { useKnowledgeBaseApi } from "@/hooks/use-knowledge-base-api"

export function KnowledgeBaseModal({ 
  open, 
  onClose, 
  onUploadComplete
}: KnowledgeBaseModalProps) {
  const { t } = useTranslation()
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const { getPresignedUrl, uploadToS3, processDocument } = useKnowledgeBaseApi()

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i]
  }

  const generateFileId = () => `f${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

  const uploadFile = async (fileId: string) => {
    const fileToUpload = files.find(f => f.id === fileId)
    if (!fileToUpload) return

    try {
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, status: "uploading" as const, progress: 10 } : f
      ))

      const presignedData = await getPresignedUrl(fileToUpload.fileName)
      
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, progress: 50 } : f
      ))

      await uploadToS3(fileToUpload.file, presignedData)
      const s3Key = presignedData.presigned_post.fields.key
      
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, status: "uploaded" as const, progress: 70, s3Key } : f
      ))

      console.log("Processing document...")
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, status: "processing" as const, progress: 85 } : f
      ))

      await processDocument(s3Key, fileToUpload.metadata)

      console.log("Upload and processing completed successfully!")
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, status: "completed" as const, progress: 100 } : f
      ))

    } catch (error) {
      console.error("Upload failed:", error)
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, status: "error" as const } : f
      ))
    }
  }

  const handleFileSelect = (selectedFiles: FileList | null) => {
    if (!selectedFiles) return

    const newFiles: UploadedFile[] = Array.from(selectedFiles).map((file) => ({
      id: generateFileId(),
      name: file.name,
      fileName: file.name,
      size: formatFileSize(file.size),
      status: "ready" as const,
      progress: 0,
      file,
      metadata: {
        filename: file.name.replace(/\.[^/.]+$/, ""), // Remove file extension
        doc_key: file.name.toLowerCase().replace(/[^a-z0-9]/g, "_").replace(/_{2,}/g, "_").replace(/^_|_$/g, "")
      }
    }))

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
    setFiles(prev => prev.map(f => 
      f.id === fileId ? { ...f, fileName: newFileName } : f
    ))
  }

  const updateMetadataFilename = (fileId: string, filename: string) => {
    setFiles(prev => prev.map(f => 
      f.id === fileId ? { ...f, metadata: { ...f.metadata, filename } } : f
    ))
  }

  const updateMetadataDocKey = (fileId: string, doc_key: string) => {
    setFiles(prev => prev.map(f => 
      f.id === fileId ? { ...f, metadata: { ...f.metadata, doc_key } } : f
    ))
  }

  const handleUploadComplete = async () => {
    if (files.length === 0) return

    setIsUploading(true)

    try {
      for (const file of files) {
        if (file.status !== "completed") {
          await uploadFile(file.id)
        }
      }

      // Wait a moment for all uploads to complete
      await new Promise(resolve => setTimeout(resolve, 1000))

      // Notify parent component that upload is complete
      if (onUploadComplete) {
        onUploadComplete(files.filter(f => f.status === "completed"))
      }

      setFiles([])
      setIsUploading(false)
      onClose()
    } catch (error) {
      console.error("Upload process failed:", error)
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
        <div className="flex-1 overflow-y-auto scrollbar-hide p-6 space-y-6">
          {/* File Upload Area */}
          <div className="space-y-4">
            <div className="space-y-1">
              <Label className="text-sm font-medium text-gray-700">{t('documents.uploadNewDocuments')}</Label>
              <p className="text-xs text-gray-500">{t('documents.uploadNewDocumentsDescription')}</p>
            </div>

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

              <div className="space-y-3 max-h-60 overflow-y-auto scrollbar-hide">
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
                  {t('knowledgeBase.uploadAndIndex')}
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
