# MIT No Attribution
#
# Copyright 2024 Amazon Web Services
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

import json
import os
import re

from langchain_core.example_selectors.base import BaseExampleSelector


class CharterReportsExampleSelector(BaseExampleSelector):

    def __init__(self, examples_location: str):

        self.examples = []

        all_files = os.listdir(examples_location)

        txt_example_files = [file for file in all_files if re.match("^.*\.jpeg$", file)]
        json_example_files = [file for file in all_files if re.match("^.*\.json$", file)]

        if len(txt_example_files) == len(json_example_files):
            files_samples_dict = {i + 1: {
                "exaple_receipt": f"{examples_location}/example_receipt_{i + 1}.jpeg",
                "extraction_example_file": f"{examples_location}/example_receipt_{i + 1}.json"
            } for i in range(len(txt_example_files))
            }

        else:

            raise Exception("Number of chunks does not match number of samples")

        for i in files_samples_dict.keys():
            example = {}

            with open(files_samples_dict[i]["text_chunk_file"], "r", encoding="utf-8") as file:
                example["text"] = file.read()

            with open(files_samples_dict[i]["extraction_example_file"], "r", encoding="utf-8") as file:
                example["extraction"] = json.load(file)

            self.examples.append(example)

        if len(self.examples) <= 0:
            raise Exception("No examples found")

    def aadd_example(self, example: dict[str, str]) -> any:
        """Asynchronously insert an example"""

        self.examples.append(example)

        return None

    def add_example(self, example: dict[str, str]) -> any:
        """Synchronously insert an example"""

        self.examples.append(example)

        return None

    def aselect_examples(self, input_variables: dict[str, str]) -> list[dict]:
        """Asynchronously return a list of examples"""

        # We dont care about input variables for now

        return self.examples[:input_variables["n_examples"]]

    def select_examples(self, input_variables: dict[str, str]) -> list[dict]:
        """Synchronously return a list of examples"""

        # We dont care about input variables for now

        return self.examples[:input_variables["n_examples"]]