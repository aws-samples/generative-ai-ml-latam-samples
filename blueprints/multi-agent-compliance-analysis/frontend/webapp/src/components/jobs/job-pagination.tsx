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
import { ChevronLeft, ChevronRight } from "lucide-react"
import type { JobPaginationProps } from "@/types"

export function JobPagination({
  currentPage,
  totalPages,
  startIndex,
  endIndex,
  totalItems,
  onPageChange,
}: JobPaginationProps) {
  if (totalPages <= 1) return null

  return (
    <div className="pt-4 border-t border-gray-200">
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600 font-medium">
          Showing <span className="font-semibold text-gray-900">{startIndex + 1}</span> to{" "}
          <span className="font-semibold text-gray-900">{Math.min(endIndex, totalItems)}</span> of{" "}
          <span className="font-semibold text-gray-900">{totalItems}</span> jobs
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(Math.max(currentPage - 1, 1))}
            disabled={currentPage === 1}
            className="text-sm font-medium"
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Previous
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
                  onClick={() => onPageChange(page)}
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
            onClick={() => onPageChange(Math.min(currentPage + 1, totalPages))}
            disabled={currentPage === totalPages}
            className="text-sm font-medium"
          >
            Next
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      </div>
    </div>
  )
}
