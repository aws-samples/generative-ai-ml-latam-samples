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

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

if (import.meta.env.VITE_DEBUG_API) {
  console.log("Debugging API", !!import.meta.env.VITE_DEBUG_API);
}

/**
 * Logs API operation details when VITE_DEBUG_API is enabled
 *
 * @param operation - The API operation type (GET, POST, etc)
 * @param endpoint - The API endpoint URL
 * @param data - Optional response data to log
 * @param error - Optional error object to log
 *
 * @example
 * ```ts
 * logApiOperation('GET', '/api/users', responseData);
 * logApiOperation('POST', '/api/documents', null, error);
 * ```
 */
export function logApiOperation(
  operation: string,
  endpoint: string,
  data?: unknown,
  error?: unknown,
) {
  if (!import.meta.env.VITE_DEBUG_API) return;

  const timestamp = new Date().toISOString();
  console.group(`[${timestamp}] API ${operation}: ${endpoint}`);

  if (data) {
    console.log("Data:", data);
  }

  if (error) {
    console.error("Error:", error);
  }

  console.groupEnd();
}

/**
 * Strips all attributes from a given HTML string
 *
 * @param rawHtml - The HTML string to strip attributes from
 * @returns The HTML string with all attributes removed
 */
export function stripBodyMarkup(rawHtml: string): string {
  const parser = new DOMParser();
  const doc = parser.parseFromString(rawHtml, "text/html");
  const body = doc.body;

  // Remove todos os atributos de forma recursiva
  function cleanAttributes(node: Element) {
    [...node.attributes].forEach((attr) => node.removeAttribute(attr.name));
    Array.from(node.children).forEach(cleanAttributes);
  }

  cleanAttributes(body);

  return body.innerHTML;
}
