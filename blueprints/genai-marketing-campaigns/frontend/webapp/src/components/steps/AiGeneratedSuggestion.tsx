// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { useCampaignContext, useLockStep } from "@/hooks";
import { useEffect, useRef, useState } from "react";
import Spinner from "@/components/Spinner";
import { Button } from "@/components/ui/button";
import { getCampaign, getSuggestion } from "@/lib/api";
import { Textarea } from "../ui/textarea";
import { IconBulb, IconMessage, IconRefresh } from "@tabler/icons-react";
import { Campaign } from "@/contexts/campaign-context";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export function AiGeneratedSuggestion() {
  const { campaignState, setCampaignState } = useCampaignContext();

  const intervalRef = useRef<
    string | number | ReturnType<typeof setInterval>
  >();

  const stepLock = useLockStep(2);

  const [jobStatus, setJobStatus] = useState<
    "IDLE" | "RUNNING" | "COMPLETED" | "FAILED"
  >("IDLE");

  useEffect(() => {
    const pollingInterval = 6000; //miliseconds
    const maxAttempts = 20;
    let attempts = 1;

    const pollingCallback = async (): Promise<void> => {
      console.log("Polling for changes:", `attempt ${attempts}/${maxAttempts}`);

      if (attempts < maxAttempts) {
        if (campaignState.campaign.id) {
          const campaign = (await getCampaign(
            campaignState.campaign.id,
          )) as Campaign;

          if (campaign.image_prompt !== undefined) {
            console.log("Remote changes detected. Updating local object...");
            setJobStatus("COMPLETED");
            setCampaignState((prev) => {
              return {
                ...prev,
                campaign: {
                  ...prev.campaign,
                  image_prompt: {
                    ai_prompt: campaign?.image_prompt?.ai_prompt,
                    ai_reasoning: campaign?.image_prompt?.ai_reasoning,
                    user_prompt: campaign?.image_prompt?.ai_prompt,
                  },
                },
              };
            });
          } else {
            attempts++;
            console.log("Nothing changed. Retrying...");
          }
        } else {
          throw new Error("Campaign ID not provided.");
        }
      } else {
        console.error("Polling failed.");
        setJobStatus("FAILED");
      }
    };

    const startJob = async () => {
      if (campaignState.campaign.id) {
        setCampaignState((prev) => {
          return {
            ...prev,
            loading: true,
          };
        });
        const request = await getSuggestion(
          campaignState.campaign.id,
          campaignState?.selectedReferences || [],
        );

        if (request?.statusCode === 200) {
          console.log("Successfully initiated job.");
          setJobStatus("RUNNING");
        } else {
          throw new Error("Something went wrong");
        }
      } else {
        throw new Error("Campaign ID not provided");
      }
    };

    const stopPolling = () => {
      clearInterval(intervalRef.current);
    };

    if (
      jobStatus === "IDLE" &&
      campaignState.campaign.image_prompt === undefined
    ) {
      console.log("No image_prompt on current campaign.");
      startJob();
    }

    if (jobStatus === "RUNNING") {
      console.log("Job running: schedulling polling interval.");
      intervalRef.current = setInterval(pollingCallback, pollingInterval);
    }

    if (jobStatus === "COMPLETED") {
      console.log("Polling completed!");
      setCampaignState((prev) => {
        return {
          ...prev,
          loading: false,
        };
      });
      stopPolling();
    }

    if (jobStatus === "FAILED") {
      setCampaignState((prev) => {
        return {
          ...prev,
          loading: false,
        };
      });
      stopPolling();
    }

    return () => {
      stopPolling();
    };
  }, [
    jobStatus,
    setCampaignState,
    campaignState.campaign,
    campaignState?.selectedReferences,
  ]);

  const onPromptChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setCampaignState((prev) => {
      return {
        ...prev,
        campaign: {
          ...prev.campaign,
          image_prompt: {
            ...prev.campaign.image_prompt,
            user_prompt: event.target.value,
          },
        },
      };
    });
  };
  return (
    <>
      <div className="flex flex-col gap-3">
        {campaignState.loading &&
          !campaignState.campaign.image_prompt?.ai_prompt && (
            <div className="flex gap-3">
              <Spinner className="text-yellow-400" />
              Creating AI generated creative suggestion...
            </div>
          )}

        {campaignState.campaign.image_prompt && (
          <>
            <Accordion type="single" collapsible className="w-full bg-indigo-50 rounded-lg px-3 mb-4">
              <AccordionItem value="ai-reasoning" className="border-none">
                <AccordionTrigger>
                  <div className="flex gap-2 items-center text-indigo-800 text-sm font-semibold"><IconBulb/> <span>AI Reasoning</span></div>
                </AccordionTrigger>
                <AccordionContent className="text-sm bg-indigo-100 p-3 rounded-lg text-indigo-900 mb-3">
                  <div className="whitespace-pre-wrap font-mono">
                    {campaignState.campaign.image_prompt?.ai_reasoning}
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>

            <div className="text-sm font-semibold flex items-center gap-2">
              <IconMessage/>
              AI-generated prompt:</div>
            <Textarea
              disabled={false}
              className="whitespace-pre-wrap font-mono"
              value={campaignState.campaign.image_prompt?.user_prompt}
              onChange={onPromptChange}
              rows={6}
            />

            {campaignState.campaign.image_prompt?.user_prompt !=
                  campaignState.campaign.image_prompt?.ai_prompt && (
                      <div className="flex justify-end">
                        <Button
                            className="flex gap-3"
                            variant={"secondary"}
                            onClick={() => {
                              setCampaignState((prev) => {
                                return {
                                  ...prev,
                                  campaign: {
                                    ...prev.campaign,
                                    image_prompt: {
                                      ...prev.campaign.image_prompt,
                                      user_prompt: prev.campaign.image_prompt?.ai_prompt,
                                    },
                                  },
                                };
                              });
                            }}
                        >
                          <IconRefresh/>
                          Recover AI suggestion
                        </Button>
                      </div>
                  )}

            {!stepLock && (
                  <div className="flex justify-end gap-3">
                    <Button
                        disabled={false}
                        className="flex gap-3"
                        onClick={() => {
                          setCampaignState((prev) => {
                            return {
                              ...prev,
                              loading: true,
                              currentStep: 3,
                            };
                          });
                        }}
                    >
                      {campaignState.loading && <Spinner/>}
                      {campaignState.loading
                          ? "Generating..."
                          : "Generate images"}
                    </Button>
                  </div>
              )}
            </>
        )}
      </div>
    </>
  );
}
