// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { createContext, useState } from "react";

export type Reference = {
  url: string;
  description?: string;
};

export type Campaign = {
  id?: string;
  name?: string;
  campaign_description?: string;
  objective?: string;
  node?: string;
  result?: string;
  image_references?: Reference[];
  image_prompt?: {
    ai_prompt?: string;
    ai_reasoning?: string;
    user_prompt?: string;
  };
};

export type CampaignState = {
  currentStep: number;
  loading: boolean;
  campaign: Campaign;
  selectedReferences?: string[];
};

type CampaignContextProviderProps = {
  children: React.ReactNode;
};

type CampaignContext = {
  campaignState: CampaignState;
  setCampaignState: React.Dispatch<React.SetStateAction<CampaignState>>;
};

export const CampaignContext = createContext<CampaignContext | null>(null);

export default function CampaignContextProvider({
  children,
}: CampaignContextProviderProps) {
  const [campaignState, setCampaignState] = useState<CampaignState>({
    currentStep: 0,
    loading: false,
    campaign: {
      name: "",
      campaign_description: "",
    },
  });

  return (
    <CampaignContext.Provider value={{ campaignState, setCampaignState }}>
      {children}
    </CampaignContext.Provider>
  );
}
