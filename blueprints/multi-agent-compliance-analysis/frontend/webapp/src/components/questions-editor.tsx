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

"use client"

import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { ArrowLeft, Plus, Trash2, Edit, Save, X, Play, FileText, AlertCircle } from "lucide-react"

import { Question, QuestionsEditorProps } from "@/types"

// // Mock questions data
// const mockQuestions: Question[] = [
//   {
//     id: "q1",
//     title: "What are the minimum capital requirements?",
//     description: "Identify the minimum capital requirements for financial institutions as specified in the regulation.",
//     isRequired: true,
//   },
//   {
//     id: "q2",
//     title: "What are the reporting obligations?",
//     description: "List all reporting obligations and their respective deadlines mentioned in the document.",
//     isRequired: true,
//   },
//   {
//     id: "q3",
//     title: "What penalties are defined for non-compliance?",
//     description: "Extract information about penalties, fines, or sanctions for regulatory violations.",
//     isRequired: false,
//   },
//   {
//     id: "q4",
//     title: "What are the governance requirements?",
//     description: "Identify corporate governance requirements and board composition rules.",
//     isRequired: true,
//   },
// ]

export function QuestionsEditor({ job, onBack, onRunAnalysis }: QuestionsEditorProps) {
  const [questions, setQuestions] = useState<Question[]>([])
  const [editingQuestion, setEditingQuestion] = useState<string | null>(null)
  const [newQuestion, setNewQuestion] = useState({
    title: "",
    description: "",
    isRequired: false,
  })
  const [isAddingNew, setIsAddingNew] = useState(false)

  const handleEditQuestion = (questionId: string, updates: Partial<Question>) => {
    setQuestions((prev) => prev.map((q) => (q.id === questionId ? { ...q, ...updates } : q)))
    setEditingQuestion(null)
  }

  const handleDeleteQuestion = (questionId: string) => {
    setQuestions((prev) => prev.filter((q) => q.id !== questionId))
  }

  const handleAddQuestion = () => {
    if (newQuestion.title && newQuestion.description) {
      const question: Question = {
        id: `q${Date.now()}`,
        ...newQuestion,
      }
      setQuestions((prev) => [...prev, question])
      setNewQuestion({ title: "", description: "", isRequired: false })
      setIsAddingNew(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50/50">
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="outline" size="sm" onClick={onBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Jobs
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Edit Questions</h1>
              <p className="text-gray-600 mt-1">
                {job.name} • {questions.length} questions!
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => setIsAddingNew(true)} className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Add Question
            </Button>
            <Button onClick={onRunAnalysis} className="flex items-center gap-2 bg-green-600 hover:bg-green-700">
              <Play className="w-4 h-4" />
              Run Analysis
            </Button>
          </div>
        </div>

        {/* Job Info */}
        <Card className="border-0 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <FileText className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{job.id}</h3>
                  <p className="text-sm text-gray-600">{job.files.length} files processed</p>
                </div>
              </div>
              <Badge variant="secondary" className="flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                Ready for Analysis
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Add New Question Form */}
        {isAddingNew && (
          <Card className="border-0 shadow-sm border-blue-200">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Add New Question!</CardTitle>
                <Button variant="ghost" size="sm" onClick={() => setIsAddingNew(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 p-4">
              <div className="grid gap-4">
                <div>
                  <Label htmlFor="new-title">Question Title</Label>
                  <Input
                    id="new-title"
                    value={newQuestion.title}
                    onChange={(e) => setNewQuestion((prev) => ({ ...prev, title: e.target.value }))}
                    placeholder="Enter question title..."
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="new-description">Description</Label>
                <Textarea
                  id="new-description"
                  value={newQuestion.description}
                  onChange={(e) => setNewQuestion((prev) => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe what this question should extract from the documents..."
                  rows={3}
                />
              </div>
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={newQuestion.isRequired}
                    onChange={(e) => setNewQuestion((prev) => ({ ...prev, isRequired: e.target.checked }))}
                    className="rounded"
                  />
                  Required question
                </label>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => setIsAddingNew(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleAddQuestion}>
                    <Plus className="w-4 h-4 mr-2" />
                    Add Question
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Questions List */}
        <div className="space-y-4">
          {questions.map((question, index) => (
            <Card key={question.id} className="border-0 shadow-sm">
              <CardContent className="p-4">
                {editingQuestion === question.id ? (
                  <EditQuestionForm
                    question={question}
                    onSave={(updates) => handleEditQuestion(question.id, updates)}
                    onCancel={() => setEditingQuestion(null)}
                  />
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-sm font-medium text-gray-500">#{index + 1}</span>
                          <h3 className="text-lg font-semibold text-gray-900">{question.title}</h3>
                          {question.isRequired && (
                            <Badge variant="secondary" className="text-xs">
                              Required
                            </Badge>
                          )}
                        </div>
                        <p className="text-gray-600 leading-relaxed">{question.description}</p>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <Button variant="ghost" size="sm" onClick={() => setEditingQuestion(question.id)}>
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteQuestion(question.id)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {questions.length === 0 && (
          <Card className="border-0 shadow-sm">
            <CardContent className="p-12 text-center">
              <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No questions yet</h3>
              <p className="text-gray-600 mb-4">Add your first question to get started with the analysis</p>
              <Button onClick={() => setIsAddingNew(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Add Question
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

function EditQuestionForm({
  question,
  onSave,
  onCancel,
}: {
  question: Question
  onSave: (updates: Partial<Question>) => void
  onCancel: () => void
}) {
  const [formData, setFormData] = useState({
    title: question.title,
    description: question.description,
    isRequired: question.isRequired,
  })

  return (
    <div className="space-y-4">
      <div className="grid gap-4">
        <div>
          <Label htmlFor="edit-title">Question Title</Label>
          <Input
            id="edit-title"
            value={formData.title}
            onChange={(e) => setFormData((prev) => ({ ...prev, title: e.target.value }))}
          />
        </div>
      </div>
      <div>
        <Label htmlFor="edit-description">Description</Label>
        <Textarea
          id="edit-description"
          value={formData.description}
          onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
          rows={3}
        />
      </div>
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={formData.isRequired}
            onChange={(e) => setFormData((prev) => ({ ...prev, isRequired: e.target.checked }))}
            className="rounded"
          />
          Required question
        </label>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onCancel}>
            <X className="w-4 h-4 mr-2" />
            Cancel
          </Button>
          <Button onClick={() => onSave(formData)}>
            <Save className="w-4 h-4 mr-2" />
            Save Changes
          </Button>
        </div>
      </div>
    </div>
  )
}
