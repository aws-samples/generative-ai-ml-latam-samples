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


singleton_instances = {}

def singleton(cls):
    global singleton_instances
    
    def get_instance(*args, **kwargs):
        if cls not in singleton_instances:
            singleton_instances[cls] = cls(*args, **kwargs)
        return singleton_instances[cls]
    return get_instance

@singleton
class KnowledgeBaseConfigSingleton:

    def __init__(
        self,
        opensearch_host,
        opensearch_port,
        opensearch_index,
        summaries_dynamodb_table
    ):
        # Initialization logic here
        self.__opensearch_host = opensearch_host
        self.__opensearch_port = opensearch_port
        self.__opensearch_index = opensearch_index
        self.__summaries_dynamodb_table = summaries_dynamodb_table

    def get_opensearch_host(self):
        return self.__opensearch_host

    def get_opensearch_port(self):
        return self.__opensearch_port

    def get_opensearch_index_name(self):
        return self.__opensearch_index

    def get_dynamodb_summaries_table_name(self):
        return self.__summaries_dynamodb_table