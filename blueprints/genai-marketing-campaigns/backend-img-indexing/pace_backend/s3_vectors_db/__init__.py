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
    Stack,
    CfnOutput,
    CfnResource,
    Fn,
)

from constructs import Construct


class S3VectorsEmbeddingsIndex(Construct):
    """A Construct that creates an Amazon S3 Vectors vector bucket and vector index.

    aws-cdk-lib 2.185.0 predates the S3 Vectors launch and has no
    ``aws_s3vectors`` L1 module, so this construct uses the generic
    ``CfnResource`` escape hatch to emit the raw CloudFormation resources
    (``AWS::S3Vectors::VectorBucket`` and ``AWS::S3Vectors::Index``), which
    CloudFormation supports natively.

    Note: bucket and index names are intentionally NOT hard-coded. Every
    ``AWS::S3Vectors::Index`` property is update-requires-Replacement, and a
    fixed name blocks CloudFormation's create-before-delete replacement flow.
    Letting CloudFormation generate the names keeps the resources replaceable;
    the generated names are exposed as attributes and stack outputs.
    """

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
    ) -> None:
        super().__init__(scope, construct_id)

        # Vector bucket to hold the embeddings index
        self.vector_bucket = CfnResource(
            self,
            "EmbeddingsVectorBucket",
            type="AWS::S3Vectors::VectorBucket",
            properties={},
        )

        # Vector index for the Titan Multimodal (1024-dim) image embeddings.
        # The text-payload metadata keys are declared non-filterable so that
        # `node`, `objective` and `results` remain filterable at query time.
        self.vector_index = CfnResource(
            self,
            "EmbeddingsVectorIndex",
            type="AWS::S3Vectors::Index",
            properties={
                "VectorBucketArn": self.vector_bucket.ref,
                "DataType": "float32",
                "Dimension": 1024,
                "DistanceMetric": "cosine",
                "MetadataConfiguration": {
                    "NonFilterableMetadataKeys": [
                        "image_s3_uri",
                        "image_description",
                        "img_element_list",
                    ],
                },
            },
        )
        self.vector_index.add_dependency(self.vector_bucket)

        # Ref returns the ARNs; derive the names from the ARN formats:
        #   bucket: arn:aws:s3vectors:<region>:<account>:bucket/<bucket-name>
        #   index:  arn:...:bucket/<bucket-name>/index/<index-name>
        self.vector_bucket_arn = self.vector_bucket.ref
        self.vector_index_arn = self.vector_index.ref
        self.vector_bucket_name = Fn.select(
            1, Fn.split("bucket/", self.vector_bucket_arn)
        )
        self.vector_index_name = Fn.select(
            1, Fn.split("/index/", self.vector_index_arn)
        )

        # Outputs
        CfnOutput(
            self,
            "VectorBucketName",
            value=self.vector_bucket_name,
            export_name=f"{Stack.of(self).stack_name}VectorBucketName",
        )

        CfnOutput(
            self,
            "VectorBucketARN",
            value=self.vector_bucket_arn,
            export_name=f"{Stack.of(self).stack_name}VectorBucketARN",
        )

        CfnOutput(
            self,
            "VectorIndexName",
            value=self.vector_index_name,
            export_name=f"{Stack.of(self).stack_name}VectorIndexName",
        )

        CfnOutput(
            self,
            "VectorIndexARN",
            value=self.vector_index_arn,
            export_name=f"{Stack.of(self).stack_name}VectorIndexARN",
        )
