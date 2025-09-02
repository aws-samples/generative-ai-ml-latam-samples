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

from aws_cdk import (
    aws_sqs as sqs,
)
from constructs import Construct

from cdk_nag import NagSuppressions, NagPackSuppression


class PACEDeadLetterQueue(sqs.DeadLetterQueue):
    def __int__(
            self,
            scope: Construct,
            construct_id: str,
            max_receive_count=1,
            **kwargs,
    ):
        queue = sqs.Queue(
            scope,
            construct_id,
            enforce_ssl=True,
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            **kwargs,
        )
        super().__init__(
            max_receive_count=max_receive_count,
            queue=queue,
        )
        NagSuppressions.add_resource_suppressions(
            construct=queue,
            suppressions=[
                NagPackSuppression(
                    id="AwsSolutions-SQS3",
                    reason="This is a DLQ",
                ),
            ],
        )


class PACEQueue(sqs.Queue):
    def __int__(
            self,
            scope: Construct,
            construct_id: str,
            dead_letter_queue: PACEDeadLetterQueue,
            **kwargs,
    ):
        super().__init__(
            scope,
            construct_id,
            enforce_ssl=True,
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            dead_letter_queue=dead_letter_queue,
            **kwargs,
        )
