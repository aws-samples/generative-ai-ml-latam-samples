// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { useContext } from "react";
import { CampaignContext } from "@/contexts/campaign-context";

export function useCampaignContext() {
  const context = useContext(CampaignContext);
  if (!context) {
    throw new Error(
      "useCampaignContext must be used within a CampaignContextProvider",
    );
  }
  return context;
}

export function useLockStep(step: number) {
  const { campaignState } = useCampaignContext();
  return campaignState.currentStep > step || campaignState.loading;
}
