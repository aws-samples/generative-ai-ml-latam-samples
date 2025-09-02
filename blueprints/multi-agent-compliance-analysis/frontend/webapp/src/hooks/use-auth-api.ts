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

import { fetchAuthSession } from "aws-amplify/auth"

export const useAuthApi = () => {
  // Centralized function to get auth token
  const getAuthToken = async (): Promise<string> => {
    const session = await fetchAuthSession()
    const token = session.tokens?.idToken?.toString()
    
    if (!token) {
      throw new Error('No authentication token available')
    }
    
    return token
  }

  // Centralized function for making authenticated API requests
  const makeAuthenticatedRequest = async (url: string, options: RequestInit = {}) => {
    const token = await getAuthToken()
    
    const defaultHeaders = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    }

    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error("Error response:", errorText)
      throw new Error(`Request failed: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }

  return {
    getAuthToken,
    makeAuthenticatedRequest,
  }
}
