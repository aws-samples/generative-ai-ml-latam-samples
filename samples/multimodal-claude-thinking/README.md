# Claude 3.7 Multimodal with Reasoning Examples

This repository demonstrates Claude 3.7's multimodal capabilities combined with explicit reasoning, showcasing three different types of interactions: text, image, and document analysis.

## Overview

The repository contains examples of using Claude 3.7 (Sonnet) to analyze different types of content while showing its reasoning process in real-time. The implementation uses AWS Bedrock and provides a clean interface for interacting with the model.

## Key Components

- `claude_think.py`: Handy class for interacting with Claude 3.7 via AWS Bedrock converse stream API. Also provide nice outputs. 

- Three example notebooks demonstrating different types of analysis:
  - `text_thinking.ipynb`: Text-based reasoning
  - `image_thinking.ipynb`: Image analysis and interpretation
  - `document_thinking.ipynb`: PDF document analysis

## Examples

### 1. Text Reasoning
[text_thinking.ipynb](text_thinking.ipynb) demonstrates Claude's ability to solve complex problems through step-by-step reasoning:
- Probability calculations
- Computer science concepts
- Mathematical problem-solving

![Text Reasoning Demo](demo_text_light.gif)

### 2. Image Analysis
[image_thinking.ipynb](image_thinking.ipynb) shows how Claude can:
- Interpret complex graphs
- Extract quantitative information
- Reconstruct visualizations with Python code

![Image Analysis Demo](demo_image_light.gif)

### 3. Document Analysis
[document_thinking.ipynb](document_thinking.ipynb) demonstrates Claude's ability to:
- Read and analyze PDF documents
- Explain complex academic papers
- Break down technical concepts into simple terms

![Document Analysis Demo](demo_document_light.gif)

### 3. PDF Analysis
[pdf_thinking.ipynb](pdf_thinking.ipynb) Same as above but extracting images and passing the images inline with document text. This is useful when you need to combine pdf text with images in the same context.

```python 
from pdf_document import PDFDocument
from claude_think import ClaudeThink
ct = ClaudeThink()
file_path = "2501.12948.pdf"
pdf_reader = PDFDocument(file_path)
content = pdf_reader.get_content_blocks() # Both text and images

reasoning, answer = ct.converse_stream(
    [
        {
            "text": "explain this paper and how compares with current benchmarks, generate a simple but correct summarization for future reference"
        },
        *content
    ]
)
...
reasoning, answer = ct.converse_stream(
    [
        {
            "text": "explain figure 3 in detail, give me a python code to replicate"
        }
    ]
)

```




## Requirements

- Python 
- AWS account with Bedrock and Model access
- Required Python packages are in `requirements.txt`

## Usage

Each notebook can be run independently. The `ClaudeThink` class in `claude_think.py` provides the core functionality for:
- Managing conversations with Claude
- Handling different types of input (text, images, documents)
- Displaying real-time reasoning process
- Formatting responses

