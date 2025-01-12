# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: LicenseRef-.amazon.com.-AmznSL-1.0
# Licensed under the Amazon Software License  http://aws.amazon.com/asl/

from pydantic import BaseModel, Field

class MetaPrompt(BaseModel):
    """A prompt for instructing a text-to-image foundation model to generate an image"""
    reasoning: str = Field(description="The reasoning/logic behind the created prompt")
    prompt: str = Field(description="The generated prompt. The prompt will be consumed by a foundation model")