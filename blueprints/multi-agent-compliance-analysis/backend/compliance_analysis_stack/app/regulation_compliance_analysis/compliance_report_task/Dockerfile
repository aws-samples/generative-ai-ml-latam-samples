# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

FROM python:3.12-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache pip install -r ./requirements.txt

COPY compliance_analysis ./compliance_analysis/
