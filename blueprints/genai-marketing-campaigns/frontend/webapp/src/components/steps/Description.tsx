// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useCampaignContext, useLockStep } from "@/hooks";
import { Button } from "@/components/ui/button";
import Spinner from "@/components/Spinner";
import { createCampaign } from "@/lib/api";
import { Campaign } from "@/contexts/campaign-context";

export function Description() {
  const { campaignState, setCampaignState } = useCampaignContext();

  const options = {
    objectives: [
        { value: "clicks", label: "Clicks" },
        { value: "awareness", label: "Awareness" },
        { value: "likes", label: "Likes" }
    ],
    nodes: [
      { value: "followers", label: "Followers" },
      { value: "customers", label: "Customers" },
      { value: "new_customers", label: "New Customers" },
    ]
  };

  const lockStep = useLockStep(0);

  const isFormValid = () => {
    return (
      campaignState.campaign.name &&
      campaignState.campaign.campaign_description &&
      campaignState.campaign.objective &&
      campaignState.campaign.node
    );
  };

  const onDescriptionChange = (
    event: React.ChangeEvent<HTMLTextAreaElement>,
  ) => {
    setCampaignState((prev) => {
      return {
        ...prev,
        campaign: { ...prev.campaign, campaign_description: event.target.value },
      };
    });
  };

  const onObjectiveChange = (val: string) => {
    setCampaignState({
      ...campaignState,
      campaign: { ...campaignState.campaign, objective: val },
    });
  };

  const onNodeChange = (val: string) => {
    setCampaignState({
      ...campaignState,
      campaign: { ...campaignState.campaign, node: val },
    });
  };

  const submitCampaign = async () => {
    setCampaignState({ ...campaignState, loading: true });
    console.info("Creating campaign:", campaignState.campaign);
    try {
      const campaign = (await createCampaign(
        campaignState.campaign,
      )) as Campaign;
      setCampaignState({
        ...campaignState,
        loading: false,
        currentStep: 1,
        campaign: campaign,
      });
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <Textarea
        onChange={onDescriptionChange}
        value={campaignState.campaign?.campaign_description}
        placeholder="Describe your campaign"
        disabled={lockStep}
      />
      <div className="flex flex-col gap-3">
        <Label>Objective</Label>
        <Select onValueChange={onObjectiveChange} disabled={lockStep}>
          <SelectTrigger>
            <SelectValue placeholder="Objective" />
          </SelectTrigger>
          <SelectContent>
            {options.objectives.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex flex-col gap-3">
        <Label>Node</Label>
        <Select onValueChange={onNodeChange} disabled={lockStep}>
          <SelectTrigger>
            <SelectValue placeholder="Node" />
          </SelectTrigger>
          <SelectContent>
            {options.nodes.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {campaignState.currentStep === 0 && (
        <div className="flex justify-end gap-3">
          <Button
            disabled={!isFormValid() || lockStep}
            className="flex gap-3"
            onClick={submitCampaign}
          >
            {campaignState.loading && <Spinner />}
            {campaignState.loading
              ? "Saving..."
              : "Save details and search for visual references"}
          </Button>
        </div>
      )}
    </div>
  );
}
