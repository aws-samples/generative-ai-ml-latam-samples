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

import type { InternalJob } from "./jobs"
import type { FileData } from "./files"
import type { TemplateWithQuestions } from "./questions"

// Header Gradient Component
export interface HeaderGradientProps {
  lightColors?: string[]
  darkColors?: string[]
  lightOpacity?: number
  darkOpacity?: number
  animationDuration?: number
  animate?: boolean
  angle?: string
  gradientScale?: number | "auto"
  className?: string
  maskClassName?: string
}

// Job Stats Component
export interface JobStatsProps {
  jobs: InternalJob[]
}

// Job Filters Component
export interface JobFiltersProps {
  searchTerm: string
  statusFilter: string
  itemsPerPage: number
  loading: boolean
  loadingFiles: boolean
  onSearchChange: (value: string) => void
  onStatusFilterChange: (value: string) => void
  onItemsPerPageChange: (value: string) => void
  onRefresh: () => void
}

// Job Pagination Component
export interface JobPaginationProps {
  currentPage: number
  totalPages: number
  startIndex: number
  endIndex: number
  totalItems: number
  onPageChange: (page: number) => void
}

// Job Actions Component
export interface JobActionsProps {
  jobId: string
  jobStatus: string
  hasSuccessfulFiles: boolean
  reportAvailable: boolean
  isAnyJobInQuestionAnswering: boolean
  onRunAnalysis: (jobId: string) => void
  onGenerateTemplate: (jobId: string) => void
  onUploadDocuments: (jobId: string) => void
  onDownloadReport: (jobId: string) => void
}

// Job Files List Component
export interface JobFilesListProps {
  files: FileData[]
  loading: boolean
  onUploadDocuments: () => void
}

// Job Card Component
export interface JobCardProps {
  job: InternalJob
  isExpanded: boolean
  filesData: FileData[]
  loadingFiles: boolean
  questionsData?: TemplateWithQuestions
  loadingQuestions: boolean
  activeTab: string
  hasSuccessfulFiles: boolean
  isAnyJobInQuestionAnswering: boolean
  onToggleExpansion: (jobId: string) => void
  onTabChange: (jobId: string, tab: string) => void
  onRunAnalysis: (jobId: string) => void
  onGenerateTemplate: (jobId: string) => void
  onUploadDocuments: (jobId: string) => void
  onDownloadReport: (jobId: string) => void
  onUpdateQuestions: (jobId: string, questions: TemplateWithQuestions) => void
}

// Questions Tab Content Component
export interface QuestionsTabContentProps {
  jobId: string
  questionsLocked: boolean
  loadingQuestions: boolean
  questionsData: TemplateWithQuestions | undefined
  hasSuccessfulFiles: boolean
  onGenerateTemplate: (jobId: string) => void
  onUpdateQuestions: (jobId: string, updatedQuestions: TemplateWithQuestions) => void
}
