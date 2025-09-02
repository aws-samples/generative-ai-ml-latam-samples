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
import { TabsContent } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { useState } from "react"
import { useQuestionsApi } from "@/hooks/use-questions-api"
import { useToast } from "@/hooks/use-toast"
import {
  Lock,
  MessageSquare,
  RefreshCw,
  FileText,
  Edit3,
  Check,
  X,
  Plus,
  Trash2,
  AlertTriangle,
} from "lucide-react"
import type { TemplateWithQuestions, QuestionsTabContentProps } from "@/types"

export function QuestionsTabContent({
  jobId,
  questionsLocked,
  loadingQuestions,
  questionsData,
  hasSuccessfulFiles,
  onGenerateTemplate,
  onUpdateQuestions,
}: QuestionsTabContentProps) {
  const [editingQuestions, setEditingQuestions] = useState<Record<string, string>>({})
  const [editedValues, setEditedValues] = useState<Record<string, string>>({})
  const [addingToSection, setAddingToSection] = useState<string | null>(null)
  const [newQuestionValue, setNewQuestionValue] = useState<string>("")
  const [savingQuestions, setSavingQuestions] = useState<boolean>(false)
  const [deletingSection, setDeletingSection] = useState<string | null>(null)
  const [confirmDeleteSection, setConfirmDeleteSection] = useState<string | null>(null)

  const { storeQuestions } = useQuestionsApi()
  const { toast } = useToast()

  const saveQuestionsToBackend = async (updatedQuestions: TemplateWithQuestions) => {
    if (savingQuestions) return
    
    setSavingQuestions(true)
    try {
      await storeQuestions(jobId, updatedQuestions)
      toast({
        title: "Questions saved",
        description: "Your questions have been successfully saved to the backend.",
      })
    } catch (error) {
      console.error('Failed to save questions to backend:', error)
      toast({
        title: "Error saving questions",
        description: "Failed to save questions to the backend. Please try again.",
        variant: "destructive",
      })
    } finally {
      setSavingQuestions(false)
    }
  }

  const startEditing = (sectionName: string, questionIndex: number, currentQuestion: string) => {
    const key = `${sectionName}-${questionIndex}`
    setEditingQuestions(prev => ({ ...prev, [key]: currentQuestion }))
    setEditedValues(prev => ({ ...prev, [key]: currentQuestion }))
  }

  const saveQuestion = async (sectionName: string, questionIndex: number) => {
    const key = `${sectionName}-${questionIndex}`
    const editedValue = editedValues[key]
    
    if (editedValue && editedValue.trim() !== '' && questionsData) {
      console.log("Saving question:", {
        jobId,
        sectionName,
        questionIndex,
        originalQuestion: editingQuestions[key],
        newQuestion: editedValue.trim()
      })
      
      const updatedQuestions = { ...questionsData }
      if (updatedQuestions[sectionName] && updatedQuestions[sectionName].questions) {
        updatedQuestions[sectionName] = {
          ...updatedQuestions[sectionName],
          questions: [...updatedQuestions[sectionName].questions]
        }
        updatedQuestions[sectionName].questions[questionIndex] = editedValue.trim()
        onUpdateQuestions(jobId, updatedQuestions)
        
        await saveQuestionsToBackend(updatedQuestions)
      }
      
      setEditingQuestions(prev => {
        const newState = { ...prev }
        delete newState[key]
        return newState
      })
      setEditedValues(prev => {
        const newState = { ...prev }
        delete newState[key]
        return newState
      })
    }
  }

  const cancelEditing = (sectionName: string, questionIndex: number) => {
    const key = `${sectionName}-${questionIndex}`
    setEditingQuestions(prev => {
      const newState = { ...prev }
      delete newState[key]
      return newState
    })
    setEditedValues(prev => {
      const newState = { ...prev }
      delete newState[key]
      return newState
    })
  }

  const handleInputChange = (sectionName: string, questionIndex: number, value: string) => {
    const key = `${sectionName}-${questionIndex}`
    setEditedValues(prev => ({ ...prev, [key]: value }))
  }

  const startAddingQuestion = (sectionName: string) => {
    setAddingToSection(sectionName)
    setNewQuestionValue("")
  }

  const saveNewQuestion = async (sectionName: string) => {
    if (newQuestionValue.trim() !== '' && questionsData) {
      console.log("Adding new question:", {
        jobId,
        sectionName,
        newQuestion: newQuestionValue.trim()
      })
      
      const updatedQuestions = { ...questionsData }
      if (updatedQuestions[sectionName]) {
        updatedQuestions[sectionName] = {
          ...updatedQuestions[sectionName],
          questions: [
            ...(updatedQuestions[sectionName].questions || []),
            newQuestionValue.trim()
          ]
        }
        onUpdateQuestions(jobId, updatedQuestions)
        await saveQuestionsToBackend(updatedQuestions)
      }
      
      setAddingToSection(null)
      setNewQuestionValue("")
    }
  }

  const cancelAddingQuestion = () => {
    setAddingToSection(null)
    setNewQuestionValue("")
  }

  const deleteQuestion = async (sectionName: string, questionIndex: number) => {
    if (questionsData && questionsData[sectionName] && questionsData[sectionName].questions) {
      console.log("Deleting question:", {
        jobId,
        sectionName,
        questionIndex,
        deletedQuestion: questionsData[sectionName].questions[questionIndex]
      })
      
      const updatedQuestions = { ...questionsData }
      updatedQuestions[sectionName] = {
        ...updatedQuestions[sectionName],
        questions: updatedQuestions[sectionName].questions.filter((_, index) => index !== questionIndex)
      }
      onUpdateQuestions(jobId, updatedQuestions)
      await saveQuestionsToBackend(updatedQuestions)
    }
  }

  const deleteSection = async (sectionName: string) => {
    if (questionsData && questionsData[sectionName]) {
      console.log("Deleting section:", {
        jobId,
        sectionName,
        deletedSection: questionsData[sectionName]
      })
      
      try {
        setDeletingSection(sectionName)
        
        // Optimistic update - immediately update the UI
        const updatedQuestions = { ...questionsData }
        delete updatedQuestions[sectionName]
        onUpdateQuestions(jobId, updatedQuestions)
        
        // Save to backend
        await saveQuestionsToBackend(updatedQuestions)
        
        toast({
          title: "Section deleted",
          description: `The "${sectionName}" section has been successfully deleted.`,
        })
      } catch (error) {
        console.error('Error deleting section:', error)
        toast({
          title: "Error",
          description: "Failed to delete section. Please try again.",
          variant: "destructive",
        })
      } finally {
        setDeletingSection(null)
        setConfirmDeleteSection(null)
      }
    }
  }

  const handleDeleteSectionClick = (sectionName: string) => {
    setConfirmDeleteSection(sectionName)
  }

  const cancelDeleteSection = () => {
    setConfirmDeleteSection(null)
  }
  return (
    <TabsContent value="questions" className="mt-6 space-y-4">
      {questionsLocked && (
        <div className="p-4 bg-gradient-to-r from-purple-50 to-violet-50 border border-purple-200 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Lock className="w-4 h-4 text-purple-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-purple-900">Questions Locked</p>
              <p className="text-xs text-purple-700 mt-1">
                Questions are locked during analysis. Please wait for the analysis to complete.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Loading state */}
      {loadingQuestions && (
        <div className="p-8 text-center border-2 border-dashed border-gray-200 rounded-lg space-y-4">
          <div className="p-3 bg-gray-100 rounded-full w-fit mx-auto animate-spin">
            <RefreshCw className="h-6 w-6 text-gray-400" />
          </div>
          <div>
            <p className="text-gray-900 font-medium mb-1">Loading questions...</p>
            <p className="text-gray-500 text-sm">Please wait while we fetch the questions</p>
          </div>
        </div>
      )}

      {!loadingQuestions && questionsData && (() => {
        return (
          <div className="space-y-6">
            {Object.entries(questionsData)
              .sort(([, a], [, b]) => a.order - b.order)
              .map(([sectionName, section]) => {
                return (
                <div 
                  key={sectionName}
                  className="p-4 border border-gray-200 rounded-lg bg-white hover:border-gray-300 hover:shadow-sm transition-all duration-200"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-semibold text-gray-900 capitalize flex items-center">
                      <span>{sectionName}</span>
                      {section.questions && Array.isArray(section.questions) && (
                        <span className="ml-2 text-sm font-medium text-violet-600 bg-violet-100 px-2 py-0.5 rounded-full">
                          {section.questions.length} {section.questions.length === 1 ? 'question' : 'questions'}
                        </span>
                      )}
                    </h3>
                    {!questionsLocked && (
                      <div className="flex items-center gap-2">
                        {confirmDeleteSection === sectionName ? (
                          <div className="flex items-center gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                            <div className="flex items-center gap-2">
                              <AlertTriangle className="w-4 h-4 text-red-600 flex-shrink-0" />
                              <div className="text-sm">
                                <span className="text-red-800 font-medium">
                                  Delete "{sectionName}"?
                                </span>
                                {section.questions && section.questions.length > 0 && (
                                  <div className="text-red-600 text-xs mt-0.5">
                                    This will permanently remove {section.questions.length} question{section.questions.length === 1 ? '' : 's'}
                                  </div>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Button
                                size="sm"
                                onClick={() => deleteSection(sectionName)}
                                className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 h-7"
                                disabled={deletingSection === sectionName}
                              >
                                {deletingSection === sectionName ? (
                                  <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                                ) : (
                                  <Check className="w-3 h-3 mr-1" />
                                )}
                                {deletingSection === sectionName ? 'Deleting...' : 'Confirm'}
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={cancelDeleteSection}
                                className="px-3 py-1 h-7"
                                disabled={deletingSection === sectionName}
                              >
                                <X className="w-3 h-3 mr-1" />
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => startAddingQuestion(sectionName)}
                              className="text-violet-600 border-violet-200 hover:bg-violet-50 hover:border-violet-300 px-3 py-1 h-7"
                              disabled={addingToSection === sectionName || savingQuestions}
                            >
                              <Plus className="w-3 h-3 mr-1" />
                              Add Question
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeleteSectionClick(sectionName)}
                              className="text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300 px-3 py-1 h-7"
                              disabled={savingQuestions || deletingSection === sectionName}
                            >
                              <Trash2 className="w-3 h-3 mr-1" />
                              Delete Section
                            </Button>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mb-4">{section.description}</p>
                  
                  {section.questions && Array.isArray(section.questions) && section.questions.length > 0 ? (
                    <div className="space-y-3 pl-4 border-l-2 border-violet-200">
                      {section.questions.map((question, index) => {
                        const editKey = `${sectionName}-${index}`
                        const isEditing = editKey in editingQuestions
                        const editedValue = editedValues[editKey] || question
                        
                        return (
                          <div key={index} className="flex items-start gap-3 group">
                            <div className="flex-shrink-0 w-6 h-6 bg-violet-100 rounded-full flex items-center justify-center mt-0.5">
                              <span className="text-xs font-bold text-violet-600">{index + 1}</span>
                            </div>
                            
                            {isEditing ? (
                              <div className="flex-1 space-y-2">
                                <Input
                                  value={editedValue}
                                  onChange={(e) => handleInputChange(sectionName, index, e.target.value)}
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter' && editedValue.trim()) {
                                      saveQuestion(sectionName, index)
                                    } else if (e.key === 'Escape') {
                                      cancelEditing(sectionName, index)
                                    }
                                  }}
                                  className="text-sm font-medium"
                                  placeholder="Enter question..."
                                  autoFocus
                                />
                                <div className="flex gap-2">
                                  <Button
                                    size="sm"
                                    onClick={() => saveQuestion(sectionName, index)}
                                    className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 h-7"
                                    disabled={!editedValue.trim() || savingQuestions}
                                  >
                                    {savingQuestions ? (
                                      <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                                    ) : (
                                      <Check className="w-3 h-3 mr-1" />
                                    )}
                                    {savingQuestions ? 'Saving...' : 'Save'}
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => cancelEditing(sectionName, index)}
                                    className="px-3 py-1 h-7"
                                  >
                                    <X className="w-3 h-3 mr-1" />
                                    Cancel
                                  </Button>
                                </div>
                              </div>
                            ) : (
                              <div className="flex-1 flex items-start justify-between">
                                <p className="text-gray-900 leading-relaxed font-medium text-sm flex-1 pr-2">
                                  {question}
                                </p>
                                {!questionsLocked && (
                                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => startEditing(sectionName, index, question)}
                                      className="p-1 h-6 w-6 hover:bg-gray-100"
                                      disabled={savingQuestions}
                                    >
                                      <Edit3 className="w-3 h-3 text-gray-500" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => deleteQuestion(sectionName, index)}
                                      className="p-1 h-6 w-6 hover:bg-red-100"
                                      disabled={savingQuestions}
                                    >
                                      <Trash2 className="w-3 h-3 text-red-500" />
                                    </Button>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500 italic">No questions for this section</p>
                  )}

                  {/* Add new question form */}
                  {addingToSection === sectionName && (
                    <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="space-y-3">
                        <Input
                          value={newQuestionValue}
                          onChange={(e) => setNewQuestionValue(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && newQuestionValue.trim()) {
                              saveNewQuestion(sectionName)
                            } else if (e.key === 'Escape') {
                              cancelAddingQuestion()
                            }
                          }}
                          className="text-sm"
                          placeholder="Enter new question..."
                          autoFocus
                        />
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => saveNewQuestion(sectionName)}
                            className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 h-7"
                            disabled={!newQuestionValue.trim() || savingQuestions}
                          >
                            {savingQuestions ? (
                              <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                            ) : (
                              <Check className="w-3 h-3 mr-1" />
                            )}
                            {savingQuestions ? 'Adding...' : 'Add Question'}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={cancelAddingQuestion}
                            className="px-3 py-1 h-7"
                          >
                            <X className="w-3 h-3 mr-1" />
                            Cancel
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        );
      })()}

      {/* No questions available */}
      {!loadingQuestions && !questionsData && (
        <div className="p-8 text-center border-2 border-dashed border-gray-200 rounded-lg space-y-4">
          <div className="p-3 bg-gray-100 rounded-full w-fit mx-auto">
            <MessageSquare className="h-6 w-6 text-gray-400" />
          </div>
          <div>
            <p className="text-gray-900 font-medium mb-1">No questions available</p>
            <p className="text-gray-500 text-sm">Generate a template to create questions</p>
          </div>
          <Button
            onClick={() => onGenerateTemplate(jobId)}
            disabled={!hasSuccessfulFiles}
            className={`text-sm font-semibold ${
              hasSuccessfulFiles
                ? "bg-blue-600 hover:bg-blue-700"
                : "bg-gray-400 cursor-not-allowed opacity-50"
            }`}
          >
            <FileText className="w-4 h-4 mr-2" />
            Generate Template
          </Button>
        </div>
      )}
    </TabsContent>
  )
}
