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
import { fetchAuthSession } from "aws-amplify/auth"
import { Navbar } from "@/components/ui/navbar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { 
  FileTextIcon, 
  RefreshCw, 
  Database, 
  FileText, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  Search,
  Filter,
} from "lucide-react"
import { NewAnalysisModal } from "@/components/new-analysis-modal"
import { KnowledgeBaseModal } from "@/components/knowledge-base-modal"

import { IngestedDocument, StatusConfig } from "@/types"

// Helper functions
const getStatusConfig = (status: string, t: (key: string) => string): StatusConfig => {
  const configs: Record<string, StatusConfig> = {
    SUCCESS: {
      label: t('knowledgeBase.status.success'),
      variant: "default" as const,
      icon: CheckCircle,
      color: "bg-green-50 text-green-700 border-green-200",
      iconColor: "bg-green-100 text-green-600",
      badgeClass: "bg-green-100 text-green-800 border-green-200",
    },
    DATA_INDEXING: {
      label: t('knowledgeBase.status.indexing'),
      variant: "secondary" as const,
      icon: Clock,
      color: "bg-blue-50 text-blue-700 border-blue-200",
      iconColor: "bg-blue-100 text-blue-600",
      badgeClass: "bg-blue-100 text-blue-800 border-blue-200",
    },
    QA_GENERATION: {
      label: t('knowledgeBase.status.qaGeneration'),
      variant: "secondary" as const,
      icon: Clock,
      color: "bg-purple-50 text-purple-700 border-purple-200",
      iconColor: "bg-purple-100 text-purple-600",
      badgeClass: "bg-purple-100 text-purple-800 border-purple-200",
    },
    ERROR: {
      label: t('knowledgeBase.status.error'),
      variant: "destructive" as const,
      icon: AlertCircle,
      color: "bg-red-50 text-red-700 border-red-200",
      iconColor: "bg-red-100 text-red-600",
      badgeClass: "bg-red-100 text-red-800 border-red-200",
    },
  }
  return configs[status] || configs.DATA_INDEXING
}

export function KnowledgeBase() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [showNewAnalysisModal, setShowNewAnalysisModal] = useState(false)
  const [showKnowledgeBaseModal, setShowKnowledgeBaseModal] = useState(false)
  
  // State for documents
  const [ingestedDocuments, setIngestedDocuments] = useState<IngestedDocument[]>([])
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // State for filtering and pagination
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(10)

  const handleCreateJob = () => {
    setShowNewAnalysisModal(false)
    navigate('/analysis')
  }

  // Handle upload completion from modal
  const handleUploadComplete = () => {
    setShowKnowledgeBaseModal(false)
    // Refresh the documents list to show newly uploaded documents
    fetchIngestedDocuments()
  }

  // Centralized function to get auth token
  const getAuthToken = async (): Promise<string> => {
    const session = await fetchAuthSession()
    const token = session.tokens?.idToken?.toString()
    
    if (!token) {
      throw new Error('No authentication token available')
    }
    
    return token
  }

  // Fetch ingested documents
  const fetchIngestedDocuments = async () => {
    try {
      setIsLoadingDocuments(true)
      setError(null)
      const token = await getAuthToken()

      const response = await fetch(
        `${import.meta.env.VITE_API_GATEWAY_REST_API_ENDPOINT_INDEX_DOCUMENTS}/compliance-report/data-indexing/jobs/query`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      )

      if (!response.ok) {
        throw new Error(`Failed to fetch documents: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      setIngestedDocuments(data.items || [])
    } catch (error) {
      console.error("Error fetching ingested documents:", error)
      setError(error instanceof Error ? error.message : 'Failed to fetch documents')
      setIngestedDocuments([])
    } finally {
      setIsLoadingDocuments(false)
    }
  }

  // Load documents on component mount
  useEffect(() => {
    fetchIngestedDocuments()
  }, [])

  // Filter and pagination logic
  const filteredDocuments = ingestedDocuments.filter((doc) => {
    const matchesSearch = 
      doc.document_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.document_key.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.document_filekey.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === "all" || doc.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const totalPages = Math.ceil(filteredDocuments.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const paginatedDocuments = filteredDocuments.slice(startIndex, endIndex)

  const handleSearchChange = (value: string) => {
    setSearchTerm(value)
    setCurrentPage(1)
  }

  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value)
    setCurrentPage(1)
  }

  return (
    <div className="h-screen bg-violet-50/30 flex flex-col overflow-hidden max-w-full">
      <Navbar 
        icon={FileTextIcon} 
        onNewAnalysis={() => setShowNewAnalysisModal(true)}
        onKnowledgeBase={() => setShowKnowledgeBaseModal(true)}
      />

      <div className="flex-1 overflow-y-auto scrollbar-hide overflow-x-hidden max-w-full">
        <div className="container mx-auto p-3 sm:p-5 space-y-4 sm:space-y-6 max-w-full overflow-x-hidden">
        {/* Stats Section */}
        <Card className="shadow-sm">
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card className="p-5 bg-violet-50 border-violet-200">
                <CardHeader className="p-0 space-y-0 pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-medium text-violet-600 uppercase tracking-wide">
                      {t('knowledgeBase.stats.totalDocuments')}
                    </CardTitle>
                    <div className="p-3 bg-violet-100 rounded-lg">
                      <Database className="h-5 w-5 text-violet-700" />
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <p className="text-3xl font-bold text-violet-900 tabular-nums mb-1">{ingestedDocuments.length}</p>
                  <p className="text-xs text-violet-700 font-medium">{t('knowledgeBase.stats.allIndexedDocuments')}</p>
                </CardContent>
              </Card>

              <Card className="p-5 bg-blue-50 border-blue-200">
                <CardHeader className="p-0 space-y-0 pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-medium text-blue-600 uppercase tracking-wide">
                      {t('knowledgeBase.stats.processing')}
                    </CardTitle>
                    <div className="p-3 bg-blue-100 rounded-lg">
                      <Clock className="h-5 w-5 text-blue-700" />
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <p className="text-3xl font-bold text-blue-900 tabular-nums mb-1">
                    {ingestedDocuments.filter((doc) => doc.status === "DATA_INDEXING" || doc.status === "QA_GENERATION").length}
                  </p>
                  <p className="text-xs text-blue-700 font-medium">{t('knowledgeBase.stats.currentlyProcessing')}</p>
                </CardContent>
              </Card>

              <Card className="p-5 bg-lime-50 border-lime-200">
                <CardHeader className="p-0 space-y-0 pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-medium text-lime-600 uppercase tracking-wide">
                      {t('knowledgeBase.stats.completed')}
                    </CardTitle>
                    <div className="p-3 bg-lime-100 rounded-lg">
                      <CheckCircle className="h-5 w-5 text-lime-700" />
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <p className="text-3xl font-bold text-lime-900 tabular-nums mb-1">
                    {ingestedDocuments.filter((doc) => doc.status === "SUCCESS").length}
                  </p>
                  <p className="text-xs text-lime-700 font-medium">{t('knowledgeBase.stats.readyForAnalysis')}</p>
                </CardContent>
              </Card>

              <Card className="p-5 bg-red-50 border-red-200">
                <CardHeader className="p-0 space-y-0 pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-medium text-red-600 uppercase tracking-wide">
                      {t('knowledgeBase.stats.errors')}
                    </CardTitle>
                    <div className="p-3 bg-red-100 rounded-lg">
                      <AlertCircle className="h-5 w-5 text-red-700" />
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <p className="text-3xl font-bold text-red-900 tabular-nums mb-1">
                    {ingestedDocuments.filter((doc) => doc.status === "ERROR").length}
                  </p>
                  <p className="text-xs text-red-700 font-medium">{t('knowledgeBase.stats.failedProcessing')}</p>
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>

        {/* Filters Card */}
        <Card className="shadow-sm">
          <CardContent className="p-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-violet-500 h-4 w-4" />
                <Input
                  placeholder={t('knowledgeBase.searchPlaceholder')}
                  value={searchTerm}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  className="pl-10 text-sm"
                />
              </div>
              <Select value={statusFilter} onValueChange={handleStatusFilterChange}>
                <SelectTrigger className="w-full sm:w-[200px] text-sm">
                  <Filter className="w-4 h-4 mr-2 text-violet-500" />
                  <SelectValue placeholder={t('knowledgeBase.filterByStatus')} />
                </SelectTrigger>
                <SelectContent className="rounded-lg">
                  <SelectItem value="all" className="text-sm rounded-md">{t('knowledgeBase.status.allStatus')}</SelectItem>
                  <SelectItem value="SUCCESS" className="text-sm rounded-md">{t('knowledgeBase.status.success')}</SelectItem>
                  <SelectItem value="DATA_INDEXING" className="text-sm rounded-md">{t('knowledgeBase.status.indexing')}</SelectItem>
                  <SelectItem value="QA_GENERATION" className="text-sm rounded-md">{t('knowledgeBase.status.qaGeneration')}</SelectItem>
                  <SelectItem value="ERROR" className="text-sm rounded-md">{t('knowledgeBase.status.error')}</SelectItem>
                </SelectContent>
              </Select>
              <Select
                value={itemsPerPage.toString()}
                onValueChange={(value) => {
                  setItemsPerPage(Number(value))
                  setCurrentPage(1)
                }}
              >
                <SelectTrigger className="w-full sm:w-[120px] text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="rounded-lg">
                  <SelectItem value="10" className="text-sm rounded-md">{t('knowledgeBase.pagination.tenPerPage')}</SelectItem>
                  <SelectItem value="20" className="text-sm rounded-md">{t('knowledgeBase.pagination.twentyPerPage')}</SelectItem>
                  <SelectItem value="50" className="text-sm rounded-md">{t('knowledgeBase.pagination.fiftyPerPage')}</SelectItem>
                </SelectContent>
              </Select>
              <Button
                onClick={fetchIngestedDocuments}
                variant="outline"
                size="sm"
                disabled={isLoadingDocuments}
                className="text-sm font-medium"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isLoadingDocuments ? 'animate-spin' : ''}`} />
                {t('knowledgeBase.refresh')}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Documents List Section */}
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-gray-900">
              {t('knowledgeBase.title')}
            </CardTitle>
            <p className="text-sm text-gray-600">
              {t('knowledgeBase.description')}
            </p>
          </CardHeader>
          <CardContent className="pt-6 space-y-5">
            {isLoadingDocuments ? (
              <div className="p-12 text-center space-y-4">
                <div className="p-3 bg-violet-100 rounded-full w-fit mx-auto animate-pulse">
                  <Database className="h-6 w-6 text-violet-600" />
                </div>
                <div>
                  <p className="text-gray-900 font-medium mb-1">{t('knowledgeBase.loadingDocuments')}</p>
                  <p className="text-gray-500 text-sm">{t('knowledgeBase.loadingDescription')}</p>
                </div>
              </div>
            ) : error ? (
              <div className="p-12 text-center border-2 border-dashed border-red-200 rounded-lg space-y-4 bg-red-50/30">
                <div className="p-3 bg-red-100 rounded-full w-fit mx-auto">
                  <AlertCircle className="h-6 w-6 text-red-600" />
                </div>
                <div>
                  <p className="text-red-900 font-medium mb-1">{t('knowledgeBase.failedToLoad')}</p>
                  <p className="text-red-700 text-sm mb-4">{error}</p>
                  <Button
                    onClick={fetchIngestedDocuments}
                    variant="outline"
                    className="text-sm font-semibold border-red-300 text-red-700 hover:bg-red-50"
                  >
                    {t('knowledgeBase.tryAgain')}
                  </Button>
                </div>
              </div>
            ) : paginatedDocuments.length === 0 ? (
              <div className="p-12 text-center border-2 border-dashed border-gray-200 rounded-lg space-y-4">
                <div className="p-3 bg-gray-100 rounded-full w-fit mx-auto">
                  <Database className="h-6 w-6 text-gray-400" />
                </div>
                <div>
                  <p className="text-gray-900 font-medium mb-1">{t('knowledgeBase.noDocuments')}</p>
                  <p className="text-gray-500 text-sm">
                    {searchTerm || statusFilter !== "all" 
                      ? t('knowledgeBase.adjustFilters')
                      : t('knowledgeBase.uploadDocuments')
                    }
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {paginatedDocuments.map((doc) => {
                  const statusConfig = getStatusConfig(doc.status, t)
                  const StatusIcon = statusConfig.icon

                  return (
                    <div
                      key={doc.job_id}
                      className={`p-4 rounded-lg border ${statusConfig.color} hover:shadow-sm transition-all duration-200`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <div className="p-1.5 bg-white rounded">
                            <FileText className="w-4 h-4 text-gray-600" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">{doc.document_name}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-xs text-gray-500 truncate">{doc.document_filekey}</span>
                              {doc.timestamp > 0 && (
                                <span className="text-xs text-gray-400">
                                  • {new Date(doc.timestamp * 1000).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-gray-400 mt-1 truncate">Key: {doc.document_key}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <StatusIcon className="w-4 h-4" />
                          <Badge className={`text-xs font-medium rounded-md ${statusConfig.badgeClass}`}>
                            {statusConfig.label}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {/* Pagination */}
            {filteredDocuments.length > 0 && totalPages > 1 && (
              <div className="pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-600 font-medium">
                    {t('knowledgeBase.pagination.showing')} <span className="font-semibold text-gray-900">{startIndex + 1}</span> {t('knowledgeBase.pagination.to')}{" "}
                    <span className="font-semibold text-gray-900">{Math.min(endIndex, filteredDocuments.length)}</span> {t('knowledgeBase.pagination.of')}{" "}
                    <span className="font-semibold text-gray-900">{filteredDocuments.length}</span> {t('knowledgeBase.pagination.documents')}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
                      disabled={currentPage === 1}
                      className="text-sm font-medium"
                    >
                      {t('knowledgeBase.pagination.previous')}
                    </Button>

                    <div className="flex items-center gap-1">
                      {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                        const showPage = page === 1 || page === totalPages || Math.abs(page - currentPage) <= 1

                        if (!showPage) {
                          if (page === 2 && currentPage > 4) {
                            return (
                              <span key={page} className="px-2 text-gray-400 text-sm">
                                ...
                              </span>
                            )
                          }
                          if (page === totalPages - 1 && currentPage < totalPages - 3) {
                            return (
                              <span key={page} className="px-2 text-gray-400 text-sm">
                                ...
                              </span>
                            )
                          }
                          return null
                        }

                        return (
                          <Button
                            key={page}
                            variant={currentPage === page ? "default" : "outline"}
                            size="sm"
                            onClick={() => setCurrentPage(page)}
                            className={`w-8 h-8 p-0 text-sm font-semibold ${
                              currentPage === page
                                ? "bg-gradient-to-r from-[#742ed1] via-[#6f37d4] to-[#4d7ceb] hover:from-[#6a29c4] hover:via-[#6530c7] hover:to-[#4570de] text-white"
                                : ""
                            }`}
                          >
                            {page}
                          </Button>
                        )
                      })}
                    </div>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
                      disabled={currentPage === totalPages}
                      className="text-sm font-medium"
                    >
                      {t('knowledgeBase.pagination.next')}
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        </div>
      </div>

      {/* New Analysis Modal */}
      <NewAnalysisModal
        open={showNewAnalysisModal}
        onClose={() => setShowNewAnalysisModal(false)}
        onCreateJob={handleCreateJob}
      />

      {/* Knowledge Base Upload Modal */}
      <KnowledgeBaseModal
        open={showKnowledgeBaseModal}
        onClose={() => setShowKnowledgeBaseModal(false)}
        onUploadComplete={handleUploadComplete}
      />
    </div>
  )
}
