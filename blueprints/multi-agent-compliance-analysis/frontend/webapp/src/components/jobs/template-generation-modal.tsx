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

import { useState, useRef } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { FileText, CheckCircle, Loader2, Upload, X, AlertCircle } from "lucide-react"
import { useAuthApi } from "@/hooks/use-auth-api"
import { getReportLayoutApiUrl } from "@/lib/api-endpoints"
import templateData from "@/lib/template.json"
import { TemplateGenerationModalProps } from "@/types"

export function TemplateGenerationModal({ 
  open, 
  onClose, 
  jobId, 
  jobName,
  onSuccess
}: TemplateGenerationModalProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [isGenerated, setIsGenerated] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [parsedJson, setParsedJson] = useState<any>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { makeAuthenticatedRequest } = useAuthApi()

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploadError(null)
    
    if (file.type !== "application/json" && !file.name.endsWith('.json')) {
      setUploadError("Please select a valid JSON file")
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string
        const jsonData = JSON.parse(content)
        setParsedJson(jsonData)
        setUploadedFile(file)
        setUploadError(null)
      } catch (error) {
        setUploadError("Invalid JSON format. Please check your file and try again.")
        setUploadedFile(null)
        setParsedJson(null)
      }
    }
    reader.readAsText(file)
  }

  const handleRemoveFile = () => {
    setUploadedFile(null)
    setParsedJson(null)
    setUploadError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const handleGenerateTemplate = async () => {
    setIsGenerating(true)
    setUploadError(null)

    try {
      // Use uploaded JSON if available, otherwise use default template
      const templatePayload = parsedJson ? {
        ...parsedJson,
        job_id: jobId
      } : {
        ...templateData,
        job_id: jobId
      }

      const apiUrl = getReportLayoutApiUrl()

      await makeAuthenticatedRequest(apiUrl, {
        method: 'POST',
        body: JSON.stringify(templatePayload)
      })

      setIsGenerated(true)
      onSuccess?.(jobId)
    } catch (error) {
      console.error('Error generating template:', error)
      setUploadError('Failed to generate template. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleClose = () => {
    setIsGenerating(false)
    setIsGenerated(false)
    setUploadedFile(null)
    setParsedJson(null)
    setUploadError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
    onClose()
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i]
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-violet-600" />
            Template Generation
          </DialogTitle>
        </DialogHeader>
        
        <div className="py-4 space-y-6">
          {!isGenerating && !isGenerated && (
            <>
              <div className="text-center space-y-2">
                <h3 className="text-lg font-semibold text-gray-900">
                  Generate Template for {jobName}
                </h3>
                <p className="text-gray-600 text-sm">
                  Job ID: {jobId}
                </p>
              </div>

              {/* File Upload Section */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-gray-700">
                    Custom Template (Optional)
                  </Label>
                  <p className="text-xs text-gray-500">
                    Upload a JSON file to use as your custom template, or leave empty to use the default template.
                  </p>
                </div>

                {!uploadedFile ? (
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                    <div className="space-y-3">
                      <div className="p-2 bg-gray-100 rounded-full w-fit mx-auto">
                        <Upload className="w-5 h-5 text-gray-600" />
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm font-medium text-gray-900">
                          Drop your JSON file here, or{" "}
                          <button
                            type="button"
                            onClick={() => fileInputRef.current?.click()}
                            className="text-violet-600 hover:text-violet-700 font-semibold"
                          >
                            browse
                          </button>
                        </p>
                        <p className="text-xs text-gray-500">JSON files only</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-1.5 bg-white rounded">
                          <FileText className="w-4 h-4 text-gray-600" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{uploadedFile.name}</p>
                          <p className="text-xs text-gray-500">{formatFileSize(uploadedFile.size)}</p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleRemoveFile}
                        className="text-gray-400 hover:text-red-600 p-1"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                )}

                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".json,application/json"
                  onChange={handleFileSelect}
                  className="hidden"
                />

                {uploadError && (
                  <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
                    <p className="text-sm text-red-700">{uploadError}</p>
                  </div>
                )}
              </div>
            </>
          )}

          {isGenerating && (
            <div className="text-center space-y-4">
              <div className="flex justify-center">
                <div className="p-4 bg-violet-100 rounded-full">
                  <Loader2 className="h-8 w-8 text-violet-600 animate-spin" />
                </div>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Generating Template
                </h3>
                <p className="text-gray-600 text-sm">
                  {uploadedFile 
                    ? `Using custom template: ${uploadedFile.name}`
                    : "Using default template"
                  }
                </p>
                <p className="text-gray-500 text-xs mt-1">
                  Job ID: {jobId}
                </p>
              </div>
            </div>
          )}

          {isGenerated && (
            <div className="text-center space-y-4">
              <div className="flex justify-center">
                <div className="p-4 bg-green-100 rounded-full">
                  <CheckCircle className="h-8 w-8 text-green-600" />
                </div>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Template Generated Successfully
                </h3>
                <p className="text-gray-600 text-sm">
                  Template has been generated for <span className="font-medium">{jobName}</span>
                </p>
                <p className="text-gray-500 text-xs mt-1">
                  {uploadedFile 
                    ? `Used custom template: ${uploadedFile.name}`
                    : "Used default template"
                  }
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3">
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isGenerating}
          >
            Cancel
          </Button>
          {!isGenerated && (
            <Button
              onClick={handleGenerateTemplate}
              disabled={isGenerating || !!uploadError}
              className="bg-violet-600 hover:bg-violet-700"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4 mr-2" />
                  Generate Template
                </>
              )}
            </Button>
          )}
          {isGenerated && (
            <Button
              onClick={handleClose}
              className="bg-violet-600 hover:bg-violet-700"
            >
              Close
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
