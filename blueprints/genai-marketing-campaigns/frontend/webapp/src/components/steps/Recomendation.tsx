// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { useCampaignContext, useLockStep } from "@/hooks";
import { useEffect, useRef, useState } from "react";
import Spinner from "@/components/Spinner";
import { Button } from "@/components/ui/button";
import { getCampaign, getReferences } from "@/lib/api";
import PresignedImage from "@/components/PresignedImage";
import { Campaign } from "@/contexts/campaign-context";

export function Recomendation() {
  const { campaignState, setCampaignState } = useCampaignContext();
  const [selectedReferences, setSelectedReferences] = useState<Set<string>>(
    new Set(),
  );

  const intervalRef = useRef<
    string | number | ReturnType<typeof setInterval>
  >();

  const stepLock = useLockStep(1);

  const toggleReference = (checked: boolean, referenceUrl: string) => {
    if (checked) {
      setSelectedReferences((prev) => {
        const newSet = new Set([...prev, referenceUrl]);
        return newSet;
      });
    } else {
      setSelectedReferences((prev) => {
        const newSet = new Set(prev);
        newSet.delete(referenceUrl);
        return newSet;
      });
    }
  };

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

          if (Array.isArray(campaign.image_references)) {
            console.log("Remote changes detected. Updating local object...");
            setJobStatus("COMPLETED");
            setCampaignState((prev) => {
              return {
                ...prev,
                campaign: {
                  ...prev.campaign,
                  image_references: campaign.image_references,
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
      console.log("Starting job...");

      if (campaignState.campaign.id) {
        setCampaignState((prev) => {
          return {
            ...prev,
            loading: true,
          };
        });
        const request = await getReferences(campaignState.campaign.id);

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
      campaignState.campaign.image_references === undefined
    ) {
      console.log("No image_references on current campaign.");
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
  }, [jobStatus, setCampaignState, campaignState.campaign]);

  return (
    <>
      <div className="flex flex-col gap-3">
        {campaignState.loading && !campaignState.campaign.image_references && (
          <div className="flex gap-3 text-sm font-bold">
            <Spinner className="text-yellow-400" />
            Searching for visual references ...
          </div>
        )}

        {campaignState.campaign.image_references && (
          <>
            {campaignState.campaign.image_references.length === 0 ? (
              <div className="rounded-md bg-gray-200 p-3 italic text-gray-600">
                No se encontraron referencias visuales.
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-6 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                {campaignState.campaign.image_references?.map(
                  (reference, idx) => {
                    return (
                      <button
                        disabled={stepLock}
                        className={`aspect-square cursor-pointer select-none overflow-hidden rounded-lg border bg-card shadow-sm disabled:cursor-default disabled:grayscale ${
                          selectedReferences.has(reference.url)
                            ? "outline-none ring-2 ring-orange-300 ring-offset-2 disabled:grayscale-0"
                            : ""
                        }`}
                        onClick={() => {
                          toggleReference(
                            !selectedReferences.has(reference.url),
                            reference.url,
                          );
                        }}
                        key={idx}
                      >
                        <div className="aspect-square">
                          <PresignedImage
                            className="h-full w-full object-scale-down"
                            s3path={reference.url}
                            fallback={<Spinner className="text-slate-700" />}
                          />
                        </div>
                      </button>
                    );
                  },
                )}
              </div>
            )}
            {!stepLock && (
              <div className="flex justify-end gap-3">
                <Button
                  disabled={stepLock}
                  className="flex gap-3"
                  onClick={() => {
                    setCampaignState((prev) => {
                      return {
                        ...prev,
                        currentStep: 2,
                        selectedReferences: [...selectedReferences],
                      };
                    });
                  }}
                >
                  Generate prompt with AI
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}
