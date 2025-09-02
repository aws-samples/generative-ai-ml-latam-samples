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

import { useState, useMemo } from "react"

interface UsePaginationProps<T> {
  items: T[]
  initialItemsPerPage?: number
}

interface UsePaginationReturn<T> {
  currentPage: number
  itemsPerPage: number
  totalPages: number
  startIndex: number
  endIndex: number
  paginatedItems: T[]
  setCurrentPage: (page: number) => void
  setItemsPerPage: (items: number) => void
  resetToFirstPage: () => void
}

export const usePagination = <T>({ 
  items, 
  initialItemsPerPage = 5 
}: UsePaginationProps<T>): UsePaginationReturn<T> => {
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(initialItemsPerPage)

  const totalPages = Math.ceil(items.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage

  const paginatedItems = useMemo(() => {
    return items.slice(startIndex, endIndex)
  }, [items, startIndex, endIndex])

  const resetToFirstPage = () => {
    setCurrentPage(1)
  }

  const handleSetItemsPerPage = (newItemsPerPage: number) => {
    setItemsPerPage(newItemsPerPage)
    setCurrentPage(1)
  }

  return {
    currentPage,
    itemsPerPage,
    totalPages,
    startIndex,
    endIndex,
    paginatedItems,
    setCurrentPage,
    setItemsPerPage: handleSetItemsPerPage,
    resetToFirstPage,
  }
}
