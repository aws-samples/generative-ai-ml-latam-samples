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

import { useState, useEffect } from "react"
import { useNavigate } from "react-router"
import { useTranslation } from "react-i18next"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Plus, FileText, XCircle, FileTextIcon } from "lucide-react"
import { Navbar } from "@/components/ui/navbar"
import { NewAnalysisModal } from "@/components/new-analysis-modal"
import { KnowledgeBaseModal } from "@/components/knowledge-base-modal"
import { JobStats, JobFilters, JobCard, JobPagination, UploadDocumentsModal, TemplateGenerationModal } from "@/components/jobs"
import type { 
  UploadedFile, 
  LegacyUploadedFile, 
  InternalJob,
} from "@/types"
import { useJobsData } from "@/hooks/use-jobs-data"
import { useFilesData } from "@/hooks/use-files-data"
import { useQuestionsData } from "@/hooks/use-questions-data"
import { useAuthApi } from "@/hooks/use-auth-api"
import { usePagination } from "@/hooks/use-pagination"
import { filterJobs, hasSuccessfulFiles } from "@/lib/job-utils"
import { getStartAnalysisApiUrl } from "@/lib/api-endpoints"

export function JobsManagement() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  
  const { jobs, loading, error, fetchJobs, handleCreateJob, updateJobStatus } = useJobsData()
  const { 
    filesData, 
    loadingFiles, 
    fetchFiles, 
    handleOptimisticFileAdd,
    handleFileStatusUpdate,
    handleOptimisticFileRemove,
    cleanupOptimisticUpdates 
  } = useFilesData()
  const { 
    questionsData, 
    loadingQuestions, 
    fetchQuestions, 
    handleUpdateQuestions,
    clearQuestionsData 
  } = useQuestionsData()
  const { makeAuthenticatedRequest } = useAuthApi()

  // Local UI state
  const [expandedJobs, setExpandedJobs] = useState<string[]>([])
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [showNewAnalysisModal, setShowNewAnalysisModal] = useState(false)
  const [showUploadDocumentsModal, setShowUploadDocumentsModal] = useState(false)
  const [showKnowledgeBaseModal, setShowKnowledgeBaseModal] = useState(false)
  const [showTemplateGenerationModal, setShowTemplateGenerationModal] = useState(false)
  const [selectedJobForUpload, setSelectedJobForUpload] = useState<string | null>(null)
  const [selectedJobForTemplate, setSelectedJobForTemplate] = useState<InternalJob | null>(null)
  const [activeTab, setActiveTab] = useState<Record<string, string>>({})

  const filteredJobs = filterJobs(jobs, searchTerm, statusFilter)
  const isAnyJobInQuestionAnswering = jobs.some(job => job.status === "question_answering")
  
  const {
    currentPage,
    itemsPerPage,
    totalPages,
    startIndex,
    endIndex,
    paginatedItems: paginatedJobs,
    setCurrentPage,
    setItemsPerPage,
    resetToFirstPage,
  } = usePagination({ items: filteredJobs })

  const fetchAllData = async () => {
    await Promise.all([fetchJobs(), fetchFiles()])
    
    clearQuestionsData()
    
    expandedJobs.forEach(jobId => {
      fetchQuestions(jobId)
    })
  }

  useEffect(() => {
    fetchAllData()
  }, [])

  useEffect(() => {
    return () => {
      cleanupOptimisticUpdates()
    }
  }, [])

  const toggleJobExpansion = (jobId: string) => {
    setExpandedJobs((prev) => {
      const newExpanded = prev.includes(jobId) ? prev.filter((id) => id !== jobId) : [...prev, jobId]

      if (!prev.includes(jobId)) {
        setActiveTab((prevTabs) => ({ ...prevTabs, [jobId]: "files" }))

        if (!questionsData[jobId]) {
          fetchQuestions(jobId)
        }
      }

      return newExpanded
    })
  }

  const handleUploadDocuments = (jobId: string): void => {
    setSelectedJobForUpload(jobId)
    setShowUploadDocumentsModal(true)
  }

  const handleKnowledgeBaseComplete = (_uploadedFiles: UploadedFile[]): void => {
   //console.log("Knowledge base upload completed")
  }

  const handleUploadComplete = (_uploadedFiles: LegacyUploadedFile[]): void => {
    fetchFiles()
    
    setSelectedJobForUpload(null)
    setShowUploadDocumentsModal(false)
  }

  const handleRunAnalysis = async (jobId: string): Promise<void> => {
    try {      
      updateJobStatus(jobId, 'analyzing')

      const payload = {
        job_id: jobId
      }

      const apiUrl = getStartAnalysisApiUrl()

      await makeAuthenticatedRequest(apiUrl, {
        method: 'POST',
        body: JSON.stringify(payload)
      })

    } catch (error) {
      console.error('Error starting analysis:', error)
      updateJobStatus(jobId, 'ready_for_analysis')
    }
  }

  const handleGenerateTemplate = async (jobId: string): Promise<void> => {
    try {
      const job = jobs.find(j => j.id === jobId)
      if (!job) {
        console.error('Job not found:', jobId)
        return
      }

      setSelectedJobForTemplate(job)
      setShowTemplateGenerationModal(true)
    } catch (error) {
      console.error('Error opening template generation modal:', error)
    }
  }

  const handleDownloadReport = async (jobId: string): Promise<void> => {
    try {
      console.log(`Report downloaded successfully for job ${jobId}`)
      // Additional logic can be added here if needed (e.g., analytics tracking)
    } catch (error) {
      console.error('Error in download report handler:', error)
    }
  }

  // Filter handlers that reset pagination
  const handleSearchChange = (value: string): void => {
    setSearchTerm(value)
    resetToFirstPage()
  }

  const handleStatusFilterChange = (value: string): void => {
    setStatusFilter(value)
    resetToFirstPage()
  }

  const handleItemsPerPageChange = (value: string): void => {
    setItemsPerPage(Number(value))
  }

  return (
    <div className="h-screen bg-violet-50/30 flex flex-col overflow-hidden max-w-full">
      <Navbar 
        icon={FileTextIcon} 
        onNewAnalysis={() => setShowNewAnalysisModal(true)}
        onKnowledgeBase={() => navigate('/knowledge-base')}
      />

      <div className="flex-1 overflow-y-auto scrollbar-hide overflow-x-hidden max-w-full">
        <div className="container mx-auto p-3 sm:p-5 space-y-4 sm:space-y-6 max-w-full overflow-x-hidden">
          {/* Stats Section */}
          <JobStats jobs={jobs} />

          {/* Filters Section */}
          <JobFilters
            searchTerm={searchTerm}
            statusFilter={statusFilter}
            itemsPerPage={itemsPerPage}
            loading={loading}
            loadingFiles={loadingFiles}
            onSearchChange={handleSearchChange}
            onStatusFilterChange={handleStatusFilterChange}
            onItemsPerPageChange={handleItemsPerPageChange}
            onRefresh={fetchAllData}
          />

          {/* Jobs Management Section */}
          <Card className="shadow-sm">
            <CardContent className="pt-6 space-y-5">
              {/* Jobs List */}
              <div className="space-y-4">
              {loading ? (
                <div className="p-12 text-center space-y-4">
                  <div className="p-3 bg-violet-100 rounded-full w-fit mx-auto animate-pulse">
                    <FileText className="h-6 w-6 text-violet-600" />
                  </div>
                  <div>
                    <p className="text-gray-900 font-medium mb-1">{t('jobs.loadingJobs')}</p>
                    <p className="text-gray-500 text-sm">{t('jobs.loadingJobsDescription')}</p>
                  </div>
                </div>
              ) : error ? (
                <div className="p-12 text-center border-2 border-dashed border-red-200 rounded-lg space-y-4 bg-red-50/30">
                  <div className="p-3 bg-red-100 rounded-full w-fit mx-auto">
                    <XCircle className="h-6 w-6 text-red-600" />
                  </div>
                  <div>
                    <p className="text-red-900 font-medium mb-1">Failed to load jobs</p>
                    <p className="text-red-700 text-sm mb-4">{error}</p>
                    <Button
                      onClick={fetchAllData}
                      variant="outline"
                      className="text-sm font-semibold border-red-300 text-red-700 hover:bg-red-50"
                    >
                      Try Again
                    </Button>
                  </div>
                </div>
              ) : paginatedJobs.length === 0 ? (
                <div className="p-12 text-center border-2 border-dashed border-gray-200 rounded-lg space-y-4">
                  <div className="p-3 bg-gray-100 rounded-full w-fit mx-auto">
                    <FileText className="h-6 w-6 text-gray-400" />
                  </div>
                  <div>
                    <p className="text-gray-900 font-medium mb-1">{t('jobs.noJobs')}</p>
                    <p className="text-gray-500 text-sm">{t('jobs.noJobsDescription')}</p>
                  </div>
                  <Button
                    onClick={() => setShowNewAnalysisModal(true)}
                    className="text-sm font-semibold bg-violet-600 hover:bg-violet-700"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    {t('jobs.createNew')}
                  </Button>
                </div>
              ) : (
                paginatedJobs.map((job) => (
                  <JobCard
                    key={job.id}
                    job={job}
                    isExpanded={expandedJobs.includes(job.id)}
                    filesData={filesData}
                    loadingFiles={loadingFiles}
                    questionsData={questionsData[job.id]}
                    loadingQuestions={loadingQuestions[job.id] || false}
                    activeTab={activeTab[job.id] || "files"}
                    hasSuccessfulFiles={hasSuccessfulFiles(job.id, filesData)}
                    isAnyJobInQuestionAnswering={isAnyJobInQuestionAnswering}
                    onToggleExpansion={toggleJobExpansion}
                    onTabChange={(jobId, tab) => setActiveTab(prev => ({ ...prev, [jobId]: tab }))}
                    onRunAnalysis={handleRunAnalysis}
                    onGenerateTemplate={handleGenerateTemplate}
                    onUploadDocuments={handleUploadDocuments}
                    onDownloadReport={handleDownloadReport}
                    onUpdateQuestions={handleUpdateQuestions}
                  />
                ))
              )}
            </div>

            {/* Pagination */}
            <JobPagination
              currentPage={currentPage}
              totalPages={totalPages}
              startIndex={startIndex}
              endIndex={endIndex}
              totalItems={filteredJobs.length}
              onPageChange={setCurrentPage}
            />
          </CardContent>
        </Card>
        </div>
      </div>

      {/* Modals */}
      <NewAnalysisModal
        open={showNewAnalysisModal}
        onClose={() => setShowNewAnalysisModal(false)}
        onCreateJob={handleCreateJob}
      />

      <KnowledgeBaseModal
        open={showKnowledgeBaseModal}
        onClose={() => setShowKnowledgeBaseModal(false)}
        onUploadComplete={handleKnowledgeBaseComplete}
      />

      <UploadDocumentsModal
        open={showUploadDocumentsModal}
        onClose={() => {
          setShowUploadDocumentsModal(false)
          setSelectedJobForUpload(null)
        }}
        onUploadComplete={handleUploadComplete}
        onOptimisticFileAdd={handleOptimisticFileAdd}
        onFileStatusUpdate={handleFileStatusUpdate}
        onOptimisticFileRemove={handleOptimisticFileRemove}
        jobId={selectedJobForUpload || undefined}
      />

      <TemplateGenerationModal
        open={showTemplateGenerationModal}
        onClose={() => {
          setShowTemplateGenerationModal(false)
          setSelectedJobForTemplate(null)
        }}
        jobId={selectedJobForTemplate?.id || ""}
        jobName={selectedJobForTemplate?.name || ""}
        onSuccess={(jobId) => {
          updateJobStatus(jobId, 'processing')
        }}
      />
    </div>
  )
}
