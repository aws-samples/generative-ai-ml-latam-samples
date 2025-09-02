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

export const downloadFileFromUrl = async (url: string, filename: string): Promise<void> => {
  try {
    const response = await fetch(url)
    
    if (!response.ok) {
      throw new Error(`Failed to download file: ${response.statusText}`)
    }

    const blob = await response.blob()
    const blobUrl = window.URL.createObjectURL(blob)
    
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = filename
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    window.URL.revokeObjectURL(blobUrl)
  } catch (error) {
    console.error('Error downloading file:', error)
    throw error
  }
}

export const extractFilenameFromUrl = (url: string, defaultName: string = 'report.md'): string => {
  try {
    const urlObj = new URL(url)
    const pathname = urlObj.pathname
    const filename = pathname.split('/').pop()
    
    if (filename && filename.includes('.')) {
      return filename
    }
    
    return defaultName
  } catch {
    return defaultName
  }
}
