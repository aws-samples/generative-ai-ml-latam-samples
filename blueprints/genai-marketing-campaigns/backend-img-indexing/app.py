#!/usr/bin/env python3

# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: LicenseRef-.amazon.com.-AmznSL-1.0
# Licensed under the Amazon Software License  http://aws.amazon.com/asl/

import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks

from pace_backend import PACEBackendStack


app = cdk.App()

main_backend_stack = PACEBackendStack(app, "GenAIMarketingCampaigns-ImgIndexStack")
cdk.Aspects.of(app).add(AwsSolutionsChecks())

app.synth()
