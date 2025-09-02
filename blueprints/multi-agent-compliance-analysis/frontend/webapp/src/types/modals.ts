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

// Modal-related type definitions
import type { InternalJob } from './jobs'
import type { UploadedFile } from './index'
import type { OptimisticFileData, FileData } from './files'

export interface NewAnalysisModalProps {
  open: boolean
  onClose: () => void
  onCreateJob: (jobData: {
    jobId: string
    analysisName: string
    workload: string
    country: string
    industry: string
    referenceQuestions: string[]
  }) => void
}

export interface TemplateGenerationModalProps {
  open: boolean
  onClose: () => void
  jobId: string
  jobName: string
  onSuccess?: (jobId: string) => void
}

export interface QuestionsEditorProps {
  job: InternalJob
  onBack: () => void
  onRunAnalysis: () => void
}

export interface KnowledgeBaseModalProps {
  open: boolean
  onClose: () => void
  onUploadComplete?: (uploadedFiles: UploadedFile[]) => void
}

export interface UploadDocumentsModalProps {
  open: boolean
  onClose: () => void
  onUploadComplete: (files: UploadedFile[]) => void
  onOptimisticFileAdd: (jobId: string, files: OptimisticFileData[]) => void
  onFileStatusUpdate: (tempJobId: string, newFileData: FileData) => void
  onOptimisticFileRemove: (tempJobId: string) => void
  jobId?: string
}
