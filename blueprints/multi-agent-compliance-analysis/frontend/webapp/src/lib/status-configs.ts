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

import { CheckCircle, XCircle, AlertCircle, Clock } from "lucide-react"

export interface StatusConfig {
  label: string
  variant: "default" | "secondary" | "outline" | "destructive"
  icon: typeof CheckCircle
  color: string
  iconColor: string
  badgeClass: string
}

export interface FileStatusConfig {
  label: string
  color: string
}

export const getStatusConfig = (status: string): StatusConfig => {
  const configs: Record<string, StatusConfig> = {
    completed: {
      label: "Completed",
      variant: "default" as const,
      icon: CheckCircle,
      color: "bg-lime-50 text-lime-700 border-lime-200",
      iconColor: "bg-lime-100 text-lime-600",
      badgeClass: "bg-gradient-to-r from-lime-500 to-lime-600 text-white border-0",
    },
    question_answering: {
      label: "Analyzing",
      variant: "outline" as const,
      icon: Clock,
      color: "bg-purple-50 text-purple-700 border-purple-200",
      iconColor: "bg-purple-100 text-purple-600",
      badgeClass: "bg-gradient-to-r from-purple-500 to-violet-600 text-white border-0",
    },
    success: {
      label: "Success",
      variant: "default" as const,
      icon: CheckCircle,
      color: "bg-green-50 text-green-700 border-green-200",
      iconColor: "bg-green-100 text-green-600",
      badgeClass: "bg-gradient-to-r from-green-500 to-emerald-600 text-white border-0",
    },
    ready_for_analysis: {
      label: "Ready for Analysis",
      variant: "secondary" as const,
      icon: AlertCircle,
      color: "bg-amber-50 text-amber-700 border-amber-200",
      iconColor: "bg-amber-100 text-amber-600",
      badgeClass: "bg-gradient-to-r from-amber-500 to-orange-500 text-white border-0",
    },
    awaiting: {
      label: "Awaiting",
      variant: "secondary" as const,
      icon: Clock,
      color: "bg-blue-50 text-blue-700 border-blue-200",
      iconColor: "bg-blue-100 text-blue-600",
      badgeClass: "bg-gradient-to-r from-blue-500 to-indigo-600 text-white border-0",
    },
    processing: {
      label: "Processing",
      variant: "outline" as const,
      icon: Clock,
      color: "bg-blue-50 text-blue-700 border-blue-200",
      iconColor: "bg-blue-100 text-blue-600",
      badgeClass: "bg-gradient-to-r from-blue-500 to-indigo-600 text-white border-0",
    },
    structuring: {
      label: "Structuring",
      variant: "outline" as const,
      icon: Clock,
      color: "bg-blue-50 text-blue-700 border-blue-200",
      iconColor: "bg-blue-100 text-blue-600",
      badgeClass: "bg-gradient-to-r from-blue-500 to-indigo-600 text-white border-0",
    },
    analyzing: {
      label: "Analyzing",
      variant: "outline" as const,
      icon: Clock,
      color: "bg-purple-50 text-purple-700 border-purple-200",
      iconColor: "bg-purple-100 text-purple-600",
      badgeClass: "bg-gradient-to-r from-purple-500 to-violet-600 text-white border-0",
    },
    error: {
      label: "Error",
      variant: "destructive" as const,
      icon: XCircle,
      color: "bg-red-50 text-red-700 border-red-200",
      iconColor: "bg-red-100 text-red-600",
      badgeClass: "bg-gradient-to-r from-red-500 to-rose-600 text-white border-0",
    },
  }
  // Try exact match first, then lowercase match for backward compatibility
  return configs[status] || configs[status.toLowerCase()] || configs.AWAITING
}

export const getFileStatusConfig = (status: string): FileStatusConfig => {
  const configs: Record<string, FileStatusConfig> = {
    completed: { label: "Completed", color: "text-lime-700 bg-lime-100" },
    success: { label: "Success", color: "text-green-700 bg-green-100" },
    processing: { label: "Processing", color: "text-blue-700 bg-blue-100" },
    queued: { label: "Queued", color: "text-slate-700 bg-slate-100" },
    error: { label: "Error", color: "text-red-700 bg-red-100" },
    page_chunking: { label: "Page Chunking", color: "text-blue-700 bg-blue-100" },
    question_persistence: { label: "Question Persistence", color: "text-purple-700 bg-purple-100" },
    question_generation: { label: "Question Generation", color: "text-indigo-700 bg-indigo-100" },
    chunk_question_generation: { label: "Chunk Question Generation", color: "text-indigo-700 bg-indigo-100" },
    document_processing: { label: "Document Processing", color: "text-orange-700 bg-orange-100" },
    uploading: { label: "Uploading", color: "text-amber-700 bg-amber-100" },
  }
  return configs[status.toLowerCase()] || configs.queued
}
