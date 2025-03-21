// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { useEffect, useState } from "react";
import { getErrorMessage } from "@/lib/utils";
import { getPresignedImageUrl } from "@/lib/api";

export type PresignedImageProps = {
  s3path: string;
  className?: string;
  fallback?: JSX.Element;
};

export default function PresignedImage({
  s3path,
  className,
  fallback,
}: PresignedImageProps) {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);
  const [signedUrl, setSignedUrl] = useState<string>("");

  useEffect(() => {
    async function getUrl() {
      try {
        const response = (await getPresignedImageUrl(s3path)) as {
          s3Path: string;
        };
        setSignedUrl(response?.s3Path);
      } catch (error) {
        setError(true);
        setSignedUrl("");
        console.error(getErrorMessage(error));
      }
    }
    getUrl();
  }, [s3path]);

  return (
    <>
      {!error && loading && (
        <div
          className={`flex h-full w-full items-center justify-center ${
            !loading && "hidden h-0 w-0 scale-0 opacity-0"
          }`}
        >
          {fallback}
        </div>
      )}
      {!error && signedUrl && (
        <img
          className={`h-0 w-0 scale-0 bg-slate-200 opacity-0 transition ${className} ${
            !loading && "h-full w-full scale-100 opacity-100"
          } `}
          src={signedUrl}
          onLoad={() => setLoading(false)}
        />
      )}
    </>
  );
}
