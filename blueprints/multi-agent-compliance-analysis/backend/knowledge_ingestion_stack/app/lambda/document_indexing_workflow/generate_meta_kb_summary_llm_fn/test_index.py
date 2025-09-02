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


import unittest
from unittest.mock import patch, MagicMock
from index import handler
import json
from io import BytesIO

class TestBedrockLambda(unittest.TestCase):
    @patch('boto3.client')
    def test_successful_invocation(self, mock_boto3_client):
        # Mock the Bedrock response
        mock_response = {
            'body': BytesIO(json.dumps({
                'completion': 'This is a test response',
                'usage': {'input_tokens': 10, 'output_tokens': 5}
            }).encode('utf-8'))
        }
        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.return_value = mock_response
        mock_boto3_client.return_value = mock_bedrock

        # Test event
        event = {
            'body': json.dumps({
                'prompt': 'Test prompt',
                'model_id': 'anthropic.claude-v2',
                'max_tokens': 100,
                'temperature': 0.5
            })
        }

        # Call the handler
        response = handler(event, None)

        # Verify response
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['response'], 'This is a test response')
        self.assertIn('usage', body)

    @patch('boto3.client')
    def test_missing_prompt(self, mock_boto3_client):
        # Test event without prompt
        event = {
            'body': json.dumps({
                'model_id': 'anthropic.claude-v2'
            })
        }

        # Call the handler
        response = handler(event, None)

        # Verify response
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], 'Prompt is required')

    @patch('boto3.client')
    def test_unsupported_model(self, mock_boto3_client):
        # Test event with unsupported model
        event = {
            'body': json.dumps({
                'prompt': 'Test prompt',
                'model_id': 'unsupported.model'
            })
        }

        # Call the handler
        response = handler(event, None)

        # Verify response
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertTrue(body['error'].startswith('Unsupported model'))

if __name__ == '__main__':
    unittest.main()