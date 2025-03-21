#!/usr/bin/env python3

# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: LicenseRef-.amazon.com.-AmznSL-1.0
# Licensed under the Amazon Software License  http://aws.amazon.com/asl/

import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks

from create_opensearch_roles.create_opensearch_roles_stack import CreateOpensearchRolesStack


app = cdk.App()
CreateOpensearchRolesStack(app, "GenAIMarketingCampaigns-CreateOpensearchRoles")
cdk.Aspects.of(app).add(AwsSolutionsChecks())

app.synth()
