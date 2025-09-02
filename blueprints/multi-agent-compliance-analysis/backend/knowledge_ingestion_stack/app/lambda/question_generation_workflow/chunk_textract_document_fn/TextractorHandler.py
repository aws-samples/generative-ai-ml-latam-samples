# MIT No Attribution
#
# Copyright 2025 Amazon Web Services
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import logging
import os

from textractor.entities.document import Document

TOKEN_WORD_RATE = os.getenv('TOKEN_WORD_RATE', 1)
MAX_TOKENS = os.getenv('MAX_TOKENS', 400)


class TextractorHandler:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def _extract_doc_chunks(self, document: Document, chunk_size: int, page_overlap: int):
        pages_doc = len(document.pages)
        self.logger.info(f'Document has {pages_doc} pages')
        self.logger.info(f'Split into {chunk_size} chunk')
        doc_chunks = []

        for i in range(0, len(document.pages), chunk_size):

            chunk = ''

            if i + chunk_size <= pages_doc:

                if i == 0:
                    chunk_pages = document.pages[i:i + chunk_size]
                else:
                    chunk_pages = document.pages[i - page_overlap:i + chunk_size]  # Page overlap

            else:
                if i == 0:
                    chunk_pages = document.pages[i:pages_doc]
                else:
                    chunk_pages = document.pages[i - page_overlap:pages_doc]  # Page overlap

            for page in chunk_pages:
                chunk = chunk + page.text

            doc_chunks.append(chunk)

        return doc_chunks

    def _extract_doc_text(self, document: Document):
        response_base = {
            'text': []
        }

        for i in range(0, len(document.pages)):
            document_page = document.pages[i]
            page_text = document_page.text
            response_base['text'].append(page_text)

        return response_base

    def get_document_text(self, document: Document, chunk_size=0, page_overlap=0):
        response_base = {
            'total_pages': len(document.pages),
            'is_in_chunks': False,
            'is_by_page': False,
            'results': {
                'text': []
            }
        }
        if chunk_size != 0:
            self.logger.info('Result is returned chunked')
            response_base['is_in_chunks'] = True
            response_base['results']['text'] = self._extract_doc_chunks(document, chunk_size, page_overlap)
        else:
            self.logger.info('Result is by page')
            response_base['is_by_page'] = True
            response_base['results'] = self._extract_doc_text(document)
        return response_base
