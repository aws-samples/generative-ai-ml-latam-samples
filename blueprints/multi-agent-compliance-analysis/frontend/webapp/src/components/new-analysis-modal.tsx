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

import { useState } from "react"
import { useTranslation } from "react-i18next"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { X, Plus, Pencil } from "lucide-react"
import referenceQuestionsData from "@/lib/reference_questions.json"
import { useNewAnalysisApi } from "@/hooks/use-new-analysis-api"
import { NewAnalysisModalProps } from "@/types"

export function NewAnalysisModal({ open, onClose, onCreateJob }: NewAnalysisModalProps) {
  const { t } = useTranslation()
  const [analysisName, setAnalysisName] = useState("")
  const [workload, setWorkload] = useState("")
  const [country, setCountry] = useState("")
  const [industry, setIndustry] = useState("")
  const [referenceQuestions, setReferenceQuestions] = useState<string[]>(referenceQuestionsData)
  const [newQuestion, setNewQuestion] = useState("")
  const [isCreating, setIsCreating] = useState(false)
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [editingQuestion, setEditingQuestion] = useState("")
  const [error, setError] = useState<string | null>(null)

  const { createAnalysisJob } = useNewAnalysisApi()

  const handleCreateJob = async () => {
    if (!analysisName.trim() || !workload.trim() || !country.trim() || !industry.trim() || referenceQuestions.length === 0) return

    setIsCreating(true)
    setError(null)

    try {
      // Prepare the payload
      const payload = {
        analysis_name: analysisName.trim(),
        workload: workload.trim(),
        country: country.trim(),
        industry: industry.trim(),
        reference_questions: referenceQuestions
      }
      
      // Make the API call using the hook
      const result = await createAnalysisJob(payload)
      
      // Extract the job ID from the API response
      const jobId = result.job_id || result.jobId || result.id
      if (!jobId) {
        throw new Error('No job ID returned from API response')
      }

      // Call the parent callback with the job data including the actual job ID
      onCreateJob({
        jobId: jobId,
        analysisName: analysisName.trim(),
        workload: workload.trim(),
        country: country.trim(),
        industry: industry.trim(),
        referenceQuestions,
      })

      setAnalysisName("")
      setWorkload("")
      setCountry("")
      setIndustry("")
      onClose()

    } catch (err) {
      console.error('Error creating job:', err)
      setError(err instanceof Error ? err.message : 'An unexpected error occurred')
    } finally {
      setIsCreating(false)
    }
  }

  const canCreateJob = analysisName.trim() && workload.trim() && country.trim() && industry.trim() && referenceQuestions.length > 0

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] mx-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="space-y-1">
            <h2 className="text-2xl font-bold text-gray-900">{t('analysis.newAnalysis')}</h2>
            <p className="text-sm text-gray-600">{t('analysis.createAnalysisDescription')}</p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <X className="h-5 w-5 text-red-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">{t('analysis.errorCreating')}</h3>
                  <div className="mt-2 text-sm text-red-700">
                    <p>{error}</p>
                  </div>
                  <div className="mt-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setError(null)}
                      className="text-red-800 border-red-300 hover:bg-red-100"
                    >
                      Dismiss
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Form Fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Analysis Name */}
            <div className="space-y-2">
              <Label htmlFor="analysis-name" className="text-sm font-medium text-gray-700">
                {t('analysis.analysisName')} *
              </Label>
              <Input
                id="analysis-name"
                value={analysisName}
                onChange={(e) => setAnalysisName(e.target.value)}
                placeholder={t('analysis.analysisNamePlaceholder')}
                className="text-sm"
                required
              />
            </div>

            {/* Workload */}
            <div className="space-y-2">
              <Label htmlFor="workload" className="text-sm font-medium text-gray-700">
                {t('analysis.workload')} *
              </Label>
              <Input
                id="workload"
                value={workload}
                onChange={(e) => setWorkload(e.target.value)}
                placeholder={t('analysis.workloadPlaceholder')}
                className="text-sm"
                required
              />
            </div>

            {/* Country */}
            <div className="space-y-2">
              <Label htmlFor="country" className="text-sm font-medium text-gray-700">
                {t('analysis.country')} *
              </Label>
              <Input
                id="country"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                placeholder={t('analysis.countryPlaceholder')}
                className="text-sm"
                required
              />
            </div>

            {/* Industry */}
            <div className="space-y-2">
              <Label htmlFor="industry" className="text-sm font-medium text-gray-700">
                {t('analysis.industry')} *
              </Label>
              <Input
                id="industry"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder={t('analysis.industryPlaceholder')}
                className="text-sm"
                required
              />
            </div>
          </div>

          {/* Reference Questions */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Label className="text-sm font-medium text-gray-700">
                  {t('analysis.referenceQuestions')} *
                </Label>
                <Badge variant="secondary" className="text-xs">
                  {t('questions.questionCount', { count: referenceQuestions.length })}
                </Badge>
              </div>
              {referenceQuestions.length > 0 && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => {
                    if (confirm(t('messages.confirmDelete'))) {
                      setReferenceQuestions([])
                    }
                  }}
                  className="text-xs text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  Remove All
                </Button>
              )}
            </div>
            <div className="border rounded-lg bg-gray-50">
              <ScrollArea className="h-[400px] p-3">
              <ul className="space-y-2 text-sm text-gray-600">
                {referenceQuestions.map((question, index) => (
                  <li key={index} className="flex items-start gap-2 group hover:bg-gray-100 p-2 rounded">
                    {editingIndex === index ? (
                      <div className="flex flex-col w-full gap-2">
                        <Input
                          value={editingQuestion}
                          onChange={(e) => setEditingQuestion(e.target.value)}
                          className="text-sm w-full"
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && editingQuestion.trim()) {
                              const newQuestions = [...referenceQuestions];
                              newQuestions[index] = editingQuestion.trim();
                              setReferenceQuestions(newQuestions);
                              setEditingIndex(null);
                            } else if (e.key === 'Escape') {
                              setEditingIndex(null);
                            }
                          }}
                        />
                        <div className="flex justify-end gap-2">
                          <Button 
                            size="sm" 
                            variant="outline" 
                            onClick={() => setEditingIndex(null)}
                            className="text-xs"
                          >
                            Cancel
                          </Button>
                          <Button 
                            size="sm" 
                            onClick={() => {
                              if (editingQuestion.trim()) {
                                const newQuestions = [...referenceQuestions];
                                newQuestions[index] = editingQuestion.trim();
                                setReferenceQuestions(newQuestions);
                                setEditingIndex(null);
                              }
                            }}
                            disabled={!editingQuestion.trim()}
                            className="text-xs bg-violet-600 hover:bg-violet-700"
                          >
                            Save
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <span className="font-medium min-w-[20px] mt-1">{index + 1}.</span>
                        <span className="flex-1">{question}</span>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setEditingQuestion(question);
                              setEditingIndex(index);
                            }}
                            className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-blue-600 p-1"
                          >
                            <Pencil className="w-3.5 h-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setReferenceQuestions(prev => prev.filter((_, i) => i !== index))
                            }}
                            className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-600 p-1"
                          >
                            <X className="w-3.5 h-3.5" />
                          </Button>
                        </div>
                      </>
                    )}
                  </li>
                ))}
              </ul>
              </ScrollArea>
            </div>
            <div className="flex gap-2 mt-2">
              <Input
                value={newQuestion}
                onChange={(e) => setNewQuestion(e.target.value)}
                placeholder={t('analysis.addQuestionPlaceholder')}
                className="text-sm flex-1"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && newQuestion.trim()) {
                    setReferenceQuestions(prev => [...prev, newQuestion.trim()])
                    setNewQuestion('')
                  }
                }}
              />
              <Button
                onClick={() => {
                  if (newQuestion.trim()) {
                    setReferenceQuestions(prev => [...prev, newQuestion.trim()])
                    setNewQuestion('')
                  }
                }}
                disabled={!newQuestion.trim()}
                className="bg-violet-600 hover:bg-violet-700"
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t bg-gray-50">
          <div className="text-sm text-gray-600">
            <span>
              {referenceQuestions.length} reference questions
            </span>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={onClose} disabled={isCreating}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateJob}
              disabled={!canCreateJob || isCreating}
              className="bg-gradient-to-r from-[#742ed1] via-[#6f37d4] to-[#4d7ceb] hover:from-[#6a29c4] hover:via-[#6530c7] hover:to-[#4570de]"
            >
              {isCreating ? (
                <>
                  <span className="mr-2 animate-spin">⏳</span>
                  {t('analysis.creating')}
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4 mr-2" />
                  {t('analysis.createAnalysis')}
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
