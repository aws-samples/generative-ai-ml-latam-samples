#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import aws_cdk as cdk

from pace_backend import PACEBackendStack
from cdk_nag import AwsSolutionsChecks

app = cdk.App()

main_backend_stack = PACEBackendStack(app, "GenAIMarketingCampaigns-ImgGenerationStack")
cdk.Aspects.of(app).add(AwsSolutionsChecks())

app.synth()
