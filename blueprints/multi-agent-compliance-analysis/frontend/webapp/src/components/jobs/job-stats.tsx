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

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { FileText, Clock, AlertCircle, CheckCircle, Brain } from "lucide-react"
import { useTranslation } from "react-i18next"
import type { JobStatsProps } from "@/types"

export function JobStats({ jobs }: JobStatsProps) {
  const { t } = useTranslation()
  
  const processingCount = jobs.filter((job) => 
    job.status === "processing" || 
    job.status === "awaiting" || 
    job.status === "AWAITING" ||
    job.status === "CHUNKING" ||
    job.status === "STRUCTURING"
  ).length
  const analyzingCount = jobs.filter((job) => 
    job.status === "analyzing" || 
    job.status === "QUESTION_ANSWERING" ||
    job.status === "REPORT_GENERATION" ||
    job.status === "question_answering" ||
    job.status === "report_generation"
  ).length
  const readyCount = jobs.filter((job) => 
    job.status === "ready_for_analysis" || 
    job.status === "READY"
  ).length
  const completedCount = jobs.filter((job) => 
    job.status === "completed" || 
    job.status === "SUCCESS"
  ).length

  return (
    <Card className="shadow-sm">
      <CardContent className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card className="p-4 bg-violet-50 border-violet-200">
            <CardHeader className="p-0 space-y-0 pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs font-medium text-violet-600 uppercase tracking-wide">
                  {t('jobs.stats.totalJobs')}
                </CardTitle>
                <div className="p-2 bg-violet-100 rounded-lg">
                  <FileText className="h-4 w-4 text-violet-700" />
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <p className="text-2xl font-bold text-violet-900 tabular-nums mb-1">{jobs.length}</p>
              <p className="text-xs text-violet-700 font-medium">{t('jobs.stats.allAnalysisJobs')}</p>
            </CardContent>
          </Card>

          <Card className="p-4 bg-blue-50 border-blue-200">
            <CardHeader className="p-0 space-y-0 pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs font-medium text-blue-600 uppercase tracking-wide">
                  {t('jobs.stats.processing')}
                </CardTitle>
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Clock className="h-4 w-4 text-blue-700" />
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <p className="text-2xl font-bold text-blue-900 tabular-nums mb-1">{processingCount}</p>
              <p className="text-xs text-blue-700 font-medium">{t('jobs.stats.currentlyProcessing')}</p>
            </CardContent>
          </Card>

          <Card className="p-4 bg-amber-50 border-amber-200">
            <CardHeader className="p-0 space-y-0 pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs font-medium text-amber-600 uppercase tracking-wide">{t('jobs.stats.ready')}</CardTitle>
                <div className="p-2 bg-amber-100 rounded-lg">
                  <AlertCircle className="h-4 w-4 text-amber-700" />
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <p className="text-2xl font-bold text-amber-900 tabular-nums mb-1">{readyCount}</p>
              <p className="text-xs text-amber-700 font-medium">{t('jobs.stats.readyForAnalysis')}</p>
            </CardContent>
          </Card>

          <Card className="p-4 bg-purple-50 border-purple-200">
            <CardHeader className="p-0 space-y-0 pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs font-medium text-purple-600 uppercase tracking-wide">
                  {t('jobs.stats.analyzing')}
                </CardTitle>
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Brain className="h-4 w-4 text-purple-700" />
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <p className="text-2xl font-bold text-purple-900 tabular-nums mb-1">{analyzingCount}</p>
              <p className="text-xs text-purple-700 font-medium">{t('jobs.stats.beingAnalyzed')}</p>
            </CardContent>
          </Card>

          <Card className="p-4 bg-lime-50 border-lime-200">
            <CardHeader className="p-0 space-y-0 pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs font-medium text-lime-600 uppercase tracking-wide">
                  {t('jobs.stats.completed')}
                </CardTitle>
                <div className="p-2 bg-lime-100 rounded-lg">
                  <CheckCircle className="h-4 w-4 text-lime-700" />
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <p className="text-2xl font-bold text-lime-900 tabular-nums mb-1">{completedCount}</p>
              <p className="text-xs text-lime-700 font-medium">{t('jobs.stats.reportsAvailable')}</p>
            </CardContent>
          </Card>
        </div>
      </CardContent>
    </Card>
  )
}
