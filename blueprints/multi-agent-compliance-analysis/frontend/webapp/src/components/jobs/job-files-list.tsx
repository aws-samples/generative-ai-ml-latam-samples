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

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { FileText, Upload } from "lucide-react"
import type { FileData, JobFilesListProps } from "@/types"
import { getFileStatusConfig } from "@/lib/status-configs"

export function JobFilesList({ files, loading, onUploadDocuments }: JobFilesListProps) {
  if (loading) {
    return (
      <div className="p-8 text-center space-y-4">
        <div className="p-3 bg-violet-100 rounded-full w-fit mx-auto animate-pulse">
          <FileText className="h-6 w-6 text-violet-600" />
        </div>
        <div>
          <p className="text-gray-900 font-medium mb-1">Loading files...</p>
          <p className="text-gray-500 text-sm">Please wait while we fetch file information</p>
        </div>
      </div>
    )
  }

  if (files.length === 0) {
    return (
      <div className="p-8 text-center border-2 border-dashed border-gray-200 rounded-lg space-y-4">
        <div className="p-3 bg-gray-100 rounded-full w-fit mx-auto">
          <FileText className="h-6 w-6 text-gray-400" />
        </div>
        <div>
          <p className="text-gray-900 font-medium mb-1">No files found</p>
          <p className="text-gray-500 text-sm">Upload documents to get started with analysis</p>
        </div>
        <Button
          onClick={onUploadDocuments}
          className="text-sm font-semibold bg-violet-600 hover:bg-violet-700"
        >
          <Upload className="w-4 h-4 mr-2" />
          Upload Documents
        </Button>
      </div>
    )
  }

  return (
    <div className="grid gap-3 max-w-full overflow-hidden">
      {files.map((file: FileData, index: number) => {
        const fileConfig = getFileStatusConfig(file.status.toLowerCase())
        const isOptimistic = file.job_id.startsWith('optimistic_')

        return (
          <div
            key={`${file.job_id}-${index}`}
            className={`flex flex-col sm:flex-row sm:items-center gap-3 p-4 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors max-w-full overflow-hidden ${
              isOptimistic ? 'animate-pulse border-amber-200 bg-amber-50/30' : ''
            }`}
          >
            <div className="flex items-center gap-3 min-w-0 flex-1 max-w-full overflow-hidden">
              <div className={`p-2.5 rounded-lg border flex-shrink-0 ${
                isOptimistic ? 'bg-amber-50 border-amber-200' : 'bg-gray-50'
              }`}>
                <FileText className={`w-4 h-4 ${
                  isOptimistic ? 'text-amber-600' : 'text-gray-600'
                }`} />
              </div>
              <div className="space-y-1 min-w-0 flex-1 max-w-full overflow-hidden">
                <div className="flex items-center gap-2 min-w-0 max-w-full overflow-hidden">
                  <p className="font-medium text-gray-900 text-sm leading-tight truncate flex-1 max-w-full" title={file.document_name}>
                    {file.document_name}
                  </p>
                  {isOptimistic && (
                    <Badge variant="secondary" className="text-xs bg-amber-100 text-amber-700 border-amber-200 flex-shrink-0">
                      Uploading
                    </Badge>
                  )}
                </div>
                <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4 text-xs text-gray-500 max-w-full overflow-hidden">
                  <div className="flex items-center gap-1 min-w-0 max-w-full overflow-hidden">
                    <span className="font-medium flex-shrink-0">Key:</span>
                    <span className="font-mono font-medium truncate max-w-32 sm:max-w-48" title={file.document_key}>
                      {file.document_key}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 min-w-0 max-w-full overflow-hidden">
                    <span className="font-medium flex-shrink-0">Job ID:</span>
                    <span className="font-mono font-medium truncate max-w-32 sm:max-w-48" title={file.job_id}>
                      {isOptimistic ? 'Processing...' : `${file.job_id.substring(0, 12)}...`}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 flex-shrink-0">
              <span
                className={`text-xs px-3 py-1.5 rounded-full font-medium border whitespace-nowrap ${fileConfig.color}`}
              >
                {file.status}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
