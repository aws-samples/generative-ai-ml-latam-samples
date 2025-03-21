// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { useEffect, useState } from "react";
import PresignedImage from "@/components/PresignedImage";
import Spinner from "../Spinner";
import { getGeneratedImage } from "@/lib/api";
import { useCampaignContext } from "@/hooks";
import { getErrorMessage } from "@/lib/utils";
import { Button } from "../ui/button";

export function AiGeneratedImages() {
  const [generatedImages, setGeneratedImages] = useState<string[]>([]);
  const [stepLoading, setStepLoading] = useState(false);
  const { campaignState } = useCampaignContext();

  const fetchImage = async () => {
    setStepLoading(true);
    try {
      const prompt =
        campaignState.campaign.image_prompt?.user_prompt != ""
          ? campaignState.campaign.image_prompt?.user_prompt
          : campaignState.campaign.image_prompt?.ai_prompt;

      if (prompt && campaignState.campaign.id) {
        const request = await getGeneratedImage(
          campaignState.campaign.id,
          prompt,
        );

        if (request?.statusCode == 200) {
          setStepLoading(false);
          const data = (await request.body.json()) as { url: string };
          setGeneratedImages((prev) => {
            return [...prev, data.url];
          });
        } else {
          throw new Error("Error asking generated image");
        }
      } else {
        throw new Error("Flow step displayed prematurely.");
      }
    } catch (error) {
      setStepLoading(false);
      console.error(getErrorMessage(error));
    }
  };

  useEffect(() => {
    for (let i = 0; i < 5; i++) {
      setTimeout(fetchImage, 200);
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="grid gap-6">
      <div className=" flex justify-end">
        <Button
          disabled={stepLoading}
          className="flex gap-3"
          onClick={() => {
            fetchImage();
          }}
        >
          {stepLoading && <Spinner />}
          {stepLoading ? "Generating..." : "Generate images"}
        </Button>
      </div>

      <div className="grid grid-cols-3 gap-6 xl:grid-cols-5">
        {generatedImages.length > 0 &&
          generatedImages.map((image) => {
            return (
              <div
                key={image}
                className="aspect-square transition-transform hover:z-50 hover:scale-150 hover:shadow-lg"
              >
                <PresignedImage
                  s3path={image}
                  className="rounded-sm"
                  fallback={<Spinner className="text-slate-700" />}
                />
              </div>
            );
          })}
      </div>
    </div>
  );
}
