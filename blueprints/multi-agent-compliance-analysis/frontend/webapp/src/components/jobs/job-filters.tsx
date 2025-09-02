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

import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Search, Filter, RefreshCw } from "lucide-react"
import type { JobFiltersProps } from "@/types"

export function JobFilters({
  searchTerm,
  statusFilter,
  itemsPerPage,
  loading,
  loadingFiles,
  onSearchChange,
  onStatusFilterChange,
  onItemsPerPageChange,
  onRefresh,
}: JobFiltersProps) {
  return (
    <Card className="shadow-sm">
      <CardContent className="p-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-violet-500 h-4 w-4" />
            <Input
              placeholder="Search by analysis name or job ID..."
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-10 text-sm"
            />
          </div>
          <Select value={statusFilter} onValueChange={onStatusFilterChange}>
            <SelectTrigger className="w-full sm:w-[200px] text-sm">
              <Filter className="w-4 h-4 mr-2 text-violet-500" />
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent className="rounded-lg">
              <SelectItem value="all" className="text-sm rounded-md">
                All Status
              </SelectItem>
              <SelectItem value="completed" className="text-sm rounded-md">
                Completed
              </SelectItem>
              <SelectItem value="ready_for_analysis" className="text-sm rounded-md">
                Ready for Analysis
              </SelectItem>
              <SelectItem value="awaiting" className="text-sm rounded-md">
                Awaiting
              </SelectItem>
              <SelectItem value="processing" className="text-sm rounded-md">
                Processing
              </SelectItem>
              <SelectItem value="structuring" className="text-sm rounded-md">
                Structuring
              </SelectItem>
              <SelectItem value="analyzing" className="text-sm rounded-md">
                Analyzing
              </SelectItem>
              <SelectItem value="error" className="text-sm rounded-md">
                Error
              </SelectItem>
            </SelectContent>
          </Select>
          <Select value={itemsPerPage.toString()} onValueChange={onItemsPerPageChange}>
            <SelectTrigger className="w-full sm:w-[120px] text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="rounded-lg">
              <SelectItem value="5" className="text-sm rounded-md">
                5 per page
              </SelectItem>
              <SelectItem value="10" className="text-sm rounded-md">
                10 per page
              </SelectItem>
              <SelectItem value="20" className="text-sm rounded-md">
                20 per page
              </SelectItem>
            </SelectContent>
          </Select>
          <Button
            onClick={onRefresh}
            variant="outline"
            size="sm"
            disabled={loading || loadingFiles}
            className="text-sm font-medium"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${(loading || loadingFiles) ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
