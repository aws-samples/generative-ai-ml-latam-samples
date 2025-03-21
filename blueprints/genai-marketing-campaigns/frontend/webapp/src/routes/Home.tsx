// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import StepContainer, { StepProps as Step } from "@/components/StepContainer";
import {
  AiGeneratedImages,
  AiGeneratedSuggestion,
  Description,
  Recomendation,
} from "@/components/steps";
import { Input } from "@/components/ui/input";
import { useCampaignContext, useLockStep } from "@/hooks";

export default function Home() {
  const { campaignState, setCampaignState } = useCampaignContext();

  const steps: Step[] = [
    {
      number: 1,
      title: "Description",
      description:
        "Use the description to drive the generation of the image",
      children: <Description />,
    },
    {
      number: 2,
      title: "Visual Suggestions",
      description:
        "Images used in previous campaigns that can be used as reference",
      children: <Recomendation />,
    },
    {
      number: 3,
      title: "AI Creative suggestion",
      children: <AiGeneratedSuggestion />,
    },
    {
      number: 4,
      title: "Generate new visual",
      children: <AiGeneratedImages />,
    },
  ];

  const onChangeName = (event: React.ChangeEvent<HTMLInputElement>) => {
    setCampaignState((prev) => {
      return {
        ...prev,
        campaign: { ...prev.campaign, name: event.target.value },
      };
    });
  };

  const lockStep = useLockStep(0);

  return (
    <div className="grid grid-flow-row gap-6">
      <header className="group flex items-center gap-1 pl-16">
        <Input
          onChange={onChangeName}
          className="bg-transparent py-6 text-2xl font-bold group-hover:bg-gray-50"
          value={campaignState.campaign?.name}
          placeholder="Campaign name"
          disabled={lockStep}
        />
      </header>

      {steps.map((step, idx) => {
        if (idx <= campaignState.currentStep)
          return (
            <StepContainer
              key={idx}
              number={step.number}
              title={step.title}
              description={step.description}
            >
              {step.children}
            </StepContainer>
          );
      })}
    </div>
  );
}
