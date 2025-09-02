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
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { ChevronDown, ChevronRight, Calendar, Files, MessageSquare, FileText, Lock, Info } from "lucide-react"
import { useTranslation } from "react-i18next"
import type { JobCardProps } from "@/types"
import { getStatusConfig } from "@/lib/status-configs"
import { getFilesForJob, getTotalQuestionsCount, isQuestionsLocked } from "@/lib/job-utils"
import { JobActions } from "./job-actions"
import { JobFilesList } from "./job-files-list"
import { QuestionsTabContent } from "./questions-tab-content"

export function JobCard({
  job,
  isExpanded,
  filesData,
  loadingFiles,
  questionsData,
  loadingQuestions,
  activeTab,
  hasSuccessfulFiles,
  isAnyJobInQuestionAnswering,
  onToggleExpansion,
  onTabChange,
  onRunAnalysis,
  onGenerateTemplate,
  onUploadDocuments,
  onDownloadReport,
  onUpdateQuestions,
}: JobCardProps) {
  const { t } = useTranslation()
  const statusConfig = getStatusConfig(job.status)
  const Icon = statusConfig.icon
  const questionsLocked = isQuestionsLocked(job.status)
  const jobFiles = getFilesForJob(job.id, filesData)
  const totalQuestions = getTotalQuestionsCount(questionsData)

  return (
    <Card
      className={`shadow-sm transition-all duration-200 max-w-full overflow-hidden ${isExpanded ? "ring-2 ring-violet-300" : ""}`}
    >
      <Collapsible open={isExpanded}>
        <CollapsibleTrigger asChild>
          <CardHeader className="pb-4 max-w-full overflow-hidden">
            <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 max-w-full overflow-hidden">
              <div className="flex items-start gap-4 flex-1 min-w-0 max-w-full overflow-hidden">
                <div className="flex items-start gap-3 pt-1 flex-shrink-0">
                  <button
                    onClick={() => onToggleExpansion(job.id)}
                    className="p-1 hover:bg-gray-100 rounded-md transition-colors"
                  >
                    {isExpanded ? (
                      <ChevronDown className="h-4 w-4 text-gray-400" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                  <div className={`p-2 rounded-lg ${statusConfig.iconColor}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                </div>

                <div className="flex-1 space-y-2 min-w-0 max-w-full overflow-hidden">
                  <div className="flex flex-wrap items-center gap-3 max-w-full overflow-hidden">
                    <CardTitle className="text-base font-semibold text-gray-900 leading-tight truncate max-w-full">
                      {job.name}
                    </CardTitle>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Badge className={`text-xs font-medium rounded-md ${statusConfig.badgeClass}`}>
                        {statusConfig.label}
                      </Badge>
                      {(job.status === "ready_for_analysis" || job.status === "READY") && (
                        <TooltipProvider delayDuration={100}>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button 
                                className="inline-flex items-center justify-center p-1 rounded-full hover:bg-blue-50 transition-colors"
                                type="button"
                              >
                                <Info className="h-4 w-4 text-blue-500 hover:text-blue-600 cursor-help" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent 
                              side="top" 
                              className="max-w-xs z-50 bg-gray-900 text-white border-gray-700 shadow-lg"
                              sideOffset={5}
                            >
                              <p className="text-sm leading-relaxed">
                                {t('jobs.runAnalysisTooltip')}
                              </p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-sm text-gray-600 max-w-full overflow-hidden">
                    <div className="flex items-center gap-1.5 min-w-0 max-w-full">
                      <span className="font-medium text-gray-500 flex-shrink-0">{t('jobs.jobId')}:</span>
                      <span className="font-mono font-medium text-gray-700 truncate max-w-32 sm:max-w-48" title={job.id}>{job.id}</span>
                    </div>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <Calendar className="h-3.5 w-3.5" />
                      <span className="font-medium">{job.createdAt}</span>
                    </div>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <Files className="h-3.5 w-3.5" />
                      <span className="font-medium">{t('jobs.filesCount', { count: jobFiles.length })}</span>
                    </div>
                    {totalQuestions > 0 && (
                      <div className="flex items-center gap-1.5 flex-shrink-0">
                        <MessageSquare className="h-3.5 w-3.5" />
                        <span className="font-medium">{t('jobs.questionsCount', { count: totalQuestions })}</span>
                      </div>
                    )}
                  </div>
                  
                  {/* Additional job information */}
                  <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-sm text-gray-600 mt-1 max-w-full overflow-hidden">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="font-medium text-gray-500 flex-shrink-0">{t('jobs.country')}:</span>
                      <span className="font-medium text-gray-700 truncate max-w-24 sm:max-w-32" title={job.country}>{job.country}</span>
                    </div>
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="font-medium text-gray-500 flex-shrink-0">{t('jobs.industry')}:</span>
                      <span className="font-medium text-gray-700 truncate max-w-24 sm:max-w-32" title={job.industry}>{job.industry}</span>
                    </div>
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="font-medium text-gray-500 flex-shrink-0">{t('jobs.workload')}:</span>
                      <span className="font-medium text-gray-700 truncate max-w-24 sm:max-w-32" title={job.workload}>{job.workload}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row items-start gap-4 pt-1 lg:pt-0 flex-shrink-0">
                <div className="text-right">
                  {/* Progress removed since we're using API file data */}
                </div>

                <JobActions
                  jobId={job.id}
                  jobStatus={job.status}
                  hasSuccessfulFiles={hasSuccessfulFiles}
                  reportAvailable={job.reportAvailable}
                  isAnyJobInQuestionAnswering={isAnyJobInQuestionAnswering}
                  onRunAnalysis={onRunAnalysis}
                  onGenerateTemplate={onGenerateTemplate}
                  onUploadDocuments={onUploadDocuments}
                  onDownloadReport={onDownloadReport}
                />
              </div>
            </div>
          </CardHeader>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="pt-0 pb-4">
            <div className="relative mb-4">
              <div className="h-0.5 bg-gradient-to-r from-transparent via-violet-400 to-transparent"></div>
              <div className="absolute inset-0 h-0.5 bg-gradient-to-r from-transparent via-violet-300/60 to-transparent blur-md"></div>
              <div className="absolute inset-0 h-px bg-gradient-to-r from-transparent via-violet-200/40 to-transparent blur-lg"></div>
            </div>

            <Tabs
              value={activeTab}
              onValueChange={(value) => onTabChange(job.id, value)}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-2 h-12 p-1.5 bg-gray-50 rounded-lg">
                <TabsTrigger
                  value="files"
                  className="flex items-center gap-2 text-sm font-medium data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-gray-900 px-4 py-2"
                >
                  <FileText className="w-4 h-4" />
                  {t('jobs.tabs.files')}
                  <Badge
                    variant="secondary"
                    className={`ml-1 text-xs ${
                      activeTab === "files" ? "bg-violet-600 text-white border-violet-600" : ""
                    }`}
                  >
                    {jobFiles.length}
                  </Badge>
                </TabsTrigger>
                <TabsTrigger
                  value="questions"
                  className="flex items-center gap-2 text-sm font-medium data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-gray-900 px-4 py-2"
                >
                  <MessageSquare className="w-4 h-4" />
                  {t('jobs.tabs.questions')}
                  <Badge
                    variant="secondary"
                    className={`ml-1 text-xs ${
                      activeTab === "questions" ? "bg-violet-600 text-white border-violet-600" : ""
                    }`}
                  >
                    {totalQuestions}
                  </Badge>
                  {questionsLocked && <Lock className="w-3 h-3 ml-1 text-gray-500" />}
                </TabsTrigger>
              </TabsList>

              <TabsContent value="files" className="mt-6 space-y-3">
                <JobFilesList
                  files={jobFiles}
                  loading={loadingFiles}
                  onUploadDocuments={() => onUploadDocuments(job.id)}
                />
              </TabsContent>

              <QuestionsTabContent
                jobId={job.id}
                questionsLocked={questionsLocked}
                loadingQuestions={loadingQuestions}
                questionsData={questionsData}
                hasSuccessfulFiles={hasSuccessfulFiles}
                onGenerateTemplate={onGenerateTemplate}
                onUpdateQuestions={onUpdateQuestions}
              />
            </Tabs>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  )
}
