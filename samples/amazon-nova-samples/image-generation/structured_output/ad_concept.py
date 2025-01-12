# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: LicenseRef-.amazon.com.-AmznSL-1.0
# Licensed under the Amazon Software License  http://aws.amazon.com/asl/

from pydantic import BaseModel, Field

class AdConcept(BaseModel):
    """A concept for a marketing campaign"""
    reasoning: str = Field(description="The reasoning/logic behind the created campaign")
    campaign_concept: str = Field(description="The main concept for the marketing campaign/advertisement")
    visual_concept: str = Field(description="The visual concept of the marketing campaign/advertisement")
    image_description: str = Field(description="The description of the image to advertise the products")
    