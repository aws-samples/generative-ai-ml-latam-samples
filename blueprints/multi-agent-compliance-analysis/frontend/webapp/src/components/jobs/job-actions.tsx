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
import { Play, FileText, Upload, Download } from "lucide-react"
import { useState } from "react"
import { useTranslation } from "react-i18next"
import { useAuthApi } from "@/hooks/use-auth-api"
import { getDownloadReportApiUrl } from "@/lib/api-endpoints"
import { downloadFileFromUrl, extractFilenameFromUrl } from "@/lib/download-utils"
import type { JobActionsProps } from "@/types"

export function JobActions({
  jobId,
  jobStatus,
  hasSuccessfulFiles,
  isAnyJobInQuestionAnswering,
  onRunAnalysis,
  onGenerateTemplate,
  onUploadDocuments,
  onDownloadReport,
}: JobActionsProps) {
  const { t } = useTranslation()
  const [isDownloading, setIsDownloading] = useState(false)
  const { makeAuthenticatedRequest } = useAuthApi()
  const isCompleted = jobStatus === "completed" || jobStatus === "SUCCESS"

  const handleDownloadReport = async () => {
    if (isDownloading) return

    try {
      setIsDownloading(true)
      
      // Call the API to get the presigned URL
      const apiUrl = getDownloadReportApiUrl(jobId)      
      const data = await makeAuthenticatedRequest(apiUrl, {
        method: 'GET',
      })
      
      if (!data.presigned_url) {
        throw new Error('No presigned URL received from server')
      }

      const filename = extractFilenameFromUrl(data.presigned_url, `report_${jobId}.md`)
            
      await downloadFileFromUrl(data.presigned_url, filename)
      onDownloadReport(jobId)
      
    } catch (error) {
      console.error('Error downloading report:', error)
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2 w-full">
      <Button
        size="sm"
        variant="outline"
        className={`text-sm font-medium bg-transparent flex-shrink-0 min-w-0 ${
          (jobStatus !== "ready_for_analysis" && jobStatus !== "READY") || isAnyJobInQuestionAnswering
            ? "opacity-50 cursor-not-allowed"
            : ""
        }`}
        disabled={(jobStatus !== "ready_for_analysis" && jobStatus !== "READY") || isAnyJobInQuestionAnswering}
        onClick={(e) => {
          e.stopPropagation()
          if ((jobStatus === "ready_for_analysis" || jobStatus === "READY") && !isAnyJobInQuestionAnswering) {
            onRunAnalysis(jobId)
          }
        }}
      >
        <Play className="w-3.5 h-3.5 mr-1.5 text-amber-600" />
        <span className="whitespace-nowrap">{t('jobs.runAnalysis')}</span>
      </Button>
      <Button
        size="sm"
        variant="outline"
        className={`text-sm font-medium bg-transparent flex-shrink-0 min-w-0 ${
          !hasSuccessfulFiles || jobStatus === "question_answering"
            ? "opacity-50 cursor-not-allowed"
            : ""
        }`}
        disabled={!hasSuccessfulFiles || jobStatus === "question_answering"}
        onClick={(e) => {
          e.stopPropagation()
          if (hasSuccessfulFiles && jobStatus !== "question_answering") {
            onGenerateTemplate(jobId)
          }
        }}
      >
        <FileText className="w-3.5 h-3.5 mr-1.5 text-blue-600" />
        <span className="whitespace-nowrap">{t('jobs.generateTemplate')}</span>
      </Button>
      <Button
        size="sm"
        variant="outline"
        className="text-sm font-medium bg-transparent flex-shrink-0 min-w-0"
        onClick={(e) => {
          e.stopPropagation()
          onUploadDocuments(jobId)
        }}
      >
        <Upload className="w-3.5 h-3.5 mr-1.5 text-violet-600" />
        <span className="whitespace-nowrap">{t('jobs.uploadDocuments')}</span>
      </Button>
      {isCompleted && (
        <Button 
          size="sm" 
          variant="outline" 
          className={`text-sm font-medium bg-transparent flex-shrink-0 min-w-0 ${
            isDownloading ? "opacity-50 cursor-not-allowed" : ""
          }`}
          disabled={isDownloading}
          onClick={(e) => {
            e.stopPropagation()
            handleDownloadReport()
          }}
        >
          <Download className={`w-3.5 h-3.5 mr-1.5 text-lime-600 ${
            isDownloading ? "animate-spin" : ""
          }`} />
          <span className="whitespace-nowrap">
            {isDownloading ? t('common.loading') : t('jobs.downloadReport')}
          </span>
        </Button>
      )}
    </div>
  )
}
